import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/customer.dart';
import '../models/conversation.dart';
import '../models/enquiry_event.dart';
import '../models/package.dart';

class SupabaseService {
  static final SupabaseService _instance = SupabaseService._internal();
  factory SupabaseService() => _instance;
  SupabaseService._internal();

  SupabaseClient get client => Supabase.instance.client;

  // ─── DASHBOARD STATS (V2) ─────────────────────────────────────────────────

  Future<Map<String, dynamic>> getDashboardStats() async {
    final customers = await getAllCustomers();

    final totalActive = customers.length;
    final onboarding = customers.where((c) => c.isOnboarding).length;
    final handoffCount = customers.where((c) => c.isHandoffActive).length;
    final appointmentCount = customers.where((c) => c.appointmentRequested).length;
    final highRisk = customers.where((c) => c.churnScore > 0.7).length;

    // AI deflection rate
    final now = DateTime.now().toUtc();
    final todayStart = DateTime.utc(now.year, now.month, now.day).toIso8601String();
    final convRes = await client
        .from('conversations')
        .select('direction, action_taken')
        .gte('timestamp', todayStart);

    final totalMessages = (convRes as List)
        .where((c) => c['direction'] == 'inbound')
        .length;
    final aiReplies = convRes
        .where((c) =>
            c['direction'] == 'outbound' && c['action_taken'] != 'human_active')
        .length;
    final humanReplies = convRes
        .where((c) =>
            c['direction'] == 'outbound' && c['action_taken'] == 'human_active')
        .length;
    final aiReplyRate = totalMessages > 0
        ? ((aiReplies / totalMessages) * 100).round()
        : 0;

    return {
      'totalActive': totalActive,
      'onboarding': onboarding,
      'handoffCount': handoffCount,
      'appointmentCount': appointmentCount,
      'highRisk': highRisk,
      'totalMessages': totalMessages,
      'aiReplies': aiReplies,
      'humanReplies': humanReplies,
      'aiReplyRate': aiReplyRate,
    };
  }

  Future<List<Map<String, dynamic>>> getMessagesByHour() async {
    final now = DateTime.now().toUtc();
    final todayStart = DateTime.utc(now.year, now.month, now.day).toIso8601String();

    final res = await client
        .from('conversations')
        .select('timestamp')
        .eq('direction', 'inbound')
        .gte('timestamp', todayStart);

    final Map<int, int> hourMap = {for (int i = 0; i < 24; i++) i: 0};
    for (final row in res as List) {
      final ts = DateTime.parse(row['timestamp'] as String);
      hourMap[ts.hour] = (hourMap[ts.hour] ?? 0) + 1;
    }
    return hourMap.entries.map((e) => {'hour': e.key, 'count': e.value}).toList();
  }

  Future<Map<String, int>> getCustomersByCategory() async {
    final res = await client.from('customers').select('churn_score');
    final Map<String, int> catMap = {'Champion': 0, 'Potential': 0, 'At Risk': 0};
    for (final row in res as List) {
      final score = (row['churn_score'] as num?)?.toDouble() ?? 0.0;
      String cat;
      if (score > 0.7) cat = 'At Risk';
      else if (score < 0.3) cat = 'Champion';
      else cat = 'Potential';
      catMap[cat] = (catMap[cat] ?? 0) + 1;
    }
    return catMap;
  }

  // ─── CONVERSATIONS ───────────────────────────────────────────────────────────

  Future<List<Conversation>> getConversations() async {
    final res = await client
        .from('conversations')
        .select('*, customers(name, preferred_country)')
        .order('timestamp', ascending: false)
        .limit(200);

    final list = (res as List).map((r) => Conversation.fromJson(r)).toList();

    // Map any missing customer names using phone numbers
    final customers = await getAllCustomers();
    final Map<String, Customer> phoneToCustomer = {
      for (var c in customers.where((c) => c.phoneNumber.isNotEmpty))
        c.phoneNumber: c
    };

    for (var conv in list) {
      if (conv.customerName == null && conv.phoneNumber != null) {
        final match = phoneToCustomer[conv.phoneNumber];
        if (match != null) {
          conv.customerName = match.name;
          conv.preferredCountry = match.preferredCountry;
          conv.customerId ??= match.id;
        }
      }
    }
    return list;
  }

  Future<List<Conversation>> getConversationsForCustomer(
      String customerId) async {
    final res = await client
        .from('conversations')
        .select('*, customers(name, preferred_country)')
        .eq('customer_id', customerId)
        .order('timestamp', ascending: true);

    final list = (res as List).map((r) => Conversation.fromJson(r)).toList();

    final cust = await getCustomerById(customerId);
    if (cust != null) {
      for (var conv in list) {
        if (conv.customerName == null) {
          conv.customerName = cust.name;
          conv.preferredCountry = cust.preferredCountry;
        }
      }
      
      // Also fetch any orphaned messages via phone number that didn't get a customer_id
      if (cust.phoneNumber.isNotEmpty) {
        final phoneRes = await client
            .from('conversations')
            .select('*, customers(name, preferred_country)')
            .eq('phone_number', cust.phoneNumber)
            .isFilter('customer_id', null)
            .order('timestamp', ascending: true);
        final phoneList = (phoneRes as List).map((r) => Conversation.fromJson(r)).toList();
        for (var conv in phoneList) {
          conv.customerName = cust.name;
          conv.preferredCountry = cust.preferredCountry;
        }
        list.addAll(phoneList);
        list.sort((a, b) => a.timestamp.compareTo(b.timestamp));
      }
    }

    return list;
  }

  Future<List<Conversation>> getConversationsByPhone(String phone) async {
    final res = await client
        .from('conversations')
        .select('*, customers(name, preferred_country)')
        .eq('phone_number', phone)
        .order('timestamp', ascending: true);
    return (res as List).map((r) => Conversation.fromJson(r)).toList();
  }

  RealtimeChannel subscribeToConversations(
      void Function(Map<String, dynamic>) onInsert) {
    return client
        .channel('conversations-realtime')
        .onPostgresChanges(
          event: PostgresChangeEvent.insert,
          schema: 'public',
          table: 'conversations',
          callback: (payload) => onInsert(payload.newRecord),
        )
        .subscribe();
  }

  // ─── CUSTOMERS ───────────────────────────────────────────────────────────────

  Future<List<Customer>> getAllCustomers() async {
    final res = await client
        .from('customers')
        .select()
        .order('last_active', ascending: false);
    return (res as List).map((r) => Customer.fromJson(r)).toList();
  }

  Future<Customer?> getCustomerById(String id) async {
    final res =
        await client.from('customers').select().eq('id', id).maybeSingle();
    if (res == null) return null;
    return Customer.fromJson(res);
  }

  Future<List<Customer>> getChurnRiskCustomers() async {
    final res = await client
        .from('customers')
        .select()
        .gt('churn_score', 0.7)
        .order('churn_score', ascending: false);
    return (res as List).map((r) => Customer.fromJson(r)).toList();
  }

  Future<List<Customer>> getHandoffCustomers() async {
    final res = await client
        .from('customers')
        .select()
        .eq('is_handoff_active', true)
        .order('last_active', ascending: false);
    return (res as List).map((r) => Customer.fromJson(r)).toList();
  }

  Future<List<Customer>> getAppointmentCustomers() async {
    final res = await client
        .from('customers')
        .select()
        .eq('appointment_requested', true)
        .order('last_active', ascending: false);
    return (res as List).map((r) => Customer.fromJson(r)).toList();
  }

  /// Get conversations that triggered voice call / follow-up intents
  Future<List<Map<String, dynamic>>> getVoiceCallConversations() async {
    final res = await client
        .from('conversations')
        .select('*, customers(id, name, phone_number, preferred_country)')
        .inFilter('action_taken', ['start_call', 'schedule_followup'])
        .order('timestamp', ascending: false)
        .limit(50);
    return (res as List).map((r) => Map<String, dynamic>.from(r)).toList();
  }

  // ─── UPDATES ────────────────────────────────────────────────────────────────

  Future<void> updateCustomerHandoff(String customerId, bool active) async {
    await client
        .from('customers')
        .update({'is_handoff_active': active})
        .eq('id', customerId);
  }

  Future<void> updateAppointmentRequested(String customerId, bool value) async {
    await client
        .from('customers')
        .update({'appointment_requested': value})
        .eq('id', customerId);
  }

  Future<void> updateCustomerField(String customerId, String field, dynamic value) async {
    await client
        .from('customers')
        .update({field: value})
        .eq('id', customerId);
  }

  Future<void> resetAllHandoffs() async {
    await client
        .from('customers')
        .update({'is_handoff_active': false})
        .eq('is_handoff_active', true);
  }

  Future<void> resetAllAppointments() async {
    await client
        .from('customers')
        .update({'appointment_requested': false})
        .eq('appointment_requested', true);
  }

  // ─── PACKAGES ────────────────────────────────────────────────────────────────

  Future<List<StudyAbroadPackage>> getAllPackages() async {
    final res = await client.from('packages').select();
    final packages =
        (res as List).map((r) => StudyAbroadPackage.fromJson(r)).toList();

    for (final pkg in packages) {
      final count = await client
          .from('customers')
          .select('id')
          .eq('preferred_country', pkg.country)
          .count(CountOption.exact);
      pkg.eligibleStudentsCount = count.count;
    }
    return packages;
  }

  // ─── ENQUIRY EVENTS ──────────────────────────────────────────────────────────

  Future<List<EnquiryEvent>> getEnquiryEventsForCustomer(
      String customerId) async {
    final res = await client
        .from('enquiry_events')
        .select()
        .eq('customer_id', customerId)
        .order('created_at', ascending: false)
        .limit(3);
    return (res as List).map((r) => EnquiryEvent.fromJson(r)).toList();
  }

  // ─── HANDOFF QUEUE (LEGACY) ─────────────────────────────────────────────────

  Future<List<Map<String, dynamic>>> getPendingHandoffs() async {
    final res = await client
        .from('handoff_queue')
        .select('*, customers!inner(name, phone_number, preferred_country, is_handoff_active)')
        .neq('status', 'resolved')
        .order('created_at', ascending: false);
    return (res as List).map((r) => Map<String, dynamic>.from(r)).toList();
  }

  /// SCANS chat history for "HANDOFF TRIGGERED" keywords that haven't been linked
  /// to a customer or a queue entry. This is a fail-safe for orphaned messages.
  Future<List<Map<String, dynamic>>> getOrphanedHandoffs() async {
    // 1. Fetch orphaned messages from the last 24 hours
    final res = await client
        .from('conversations')
        .select()
        .ilike('message_text', '%HANDOFF TRIGGERED%')
        .isFilter('customer_id', null)
        .order('timestamp', ascending: false)
        .limit(10);

    final List<Map<String, dynamic>> orphans = (res as List).map((r) => Map<String, dynamic>.from(r)).toList();
    final List<Map<String, dynamic>> rescued = [];

    // 2. Try to match each orphan to a customer via phone_number
    for (var orphan in orphans) {
      final phone = orphan['phone_number'];
      if (phone != null) {
        final custRes = await client
            .from('customers')
            .select('id, name, phone_number, preferred_country')
            .eq('phone_number', phone.toString())
            .single();
        
        if (custRes != null) {
          rescued.add({
            'source': 'chat_rescue',
            'id': 'rescue-${orphan['id']}',
            'customer_id': custRes['id'],
            'created_at': orphan['timestamp'],
            'reason': 'RESCUED: Detected in chat logs (Missing Link)',
            'customers': custRes,
          });
        }
      }
    }
    return rescued;
  }

  Future<void> handleHandoff(String handoffId) async {
    await client.from('handoff_queue').update({
      'status': 'in_progress',
    }).eq('id', handoffId);
  }

  Future<void> resolveHandoff(String handoffId, String customerId) async {
    try {
      // 1. Try to resolve the specific queue entry if it exists
      if (!handoffId.startsWith('legacy-') && !handoffId.startsWith('rescue-')) {
        await client.from('handoff_queue').update({
          'status': 'resolved',
          'resolved_at': DateTime.now().toIso8601String(),
        }).eq('id', handoffId);
      } else {
        // If it was a synthetic entry (flag-only or rescued from chat), 
        // try to resolve any pending queue items for this customer anyway
        await client.from('handoff_queue').update({
          'status': 'resolved',
          'resolved_at': DateTime.now().toIso8601String(),
        }).eq('customer_id', customerId).neq('status', 'resolved');
      }
    } catch (e) {
      // Even if history update fails, we proceed to clear the active flag
      print('Handoff history update failed (likely RLS), proceeding to clear flag: $e');
    }

    // 2. Clear the global flag in customers table (Fail-safe)
    await updateCustomerHandoff(customerId, false);
  }

  Future<void> createHandoff(
      String customerId, String reason, String? packageDiscussed) async {
    await client.from('handoff_queue').insert({
      'customer_id': customerId,
      'reason': reason,
      'package_discussed': packageDiscussed,
      'status': 'pending',
    });
    await updateCustomerHandoff(customerId, true);
  }

  RealtimeChannel subscribeToHandoffQueue(
      void Function(Map<String, dynamic>) onInsert) {
    return client
        .channel('handoff-realtime')
        .onPostgresChanges(
          event: PostgresChangeEvent.insert,
          schema: 'public',
          table: 'handoff_queue',
          callback: (payload) => onInsert(payload.newRecord),
        )
        .subscribe();
  }

  RealtimeChannel subscribeToCustomers(
      void Function(Map<String, dynamic>) onChange) {
    return client
        .channel('customers-realtime')
        .onPostgresChanges(
          event: PostgresChangeEvent.all,
          schema: 'public',
          table: 'customers',
          callback: (payload) => onChange(payload.newRecord),
        )
        .subscribe();
  }
}
