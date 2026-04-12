import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../models/customer.dart';
import '../services/supabase_service.dart';
import 'customer_profile_screen.dart';
import 'conversation_detail_screen.dart';

class HandoffQueueScreen extends StatefulWidget {
  const HandoffQueueScreen({super.key});
  @override
  State<HandoffQueueScreen> createState() => _HandoffQueueScreenState();
}

class _HandoffQueueScreenState extends State<HandoffQueueScreen> {
  List<_QueueItem> _queue = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    final svc = context.read<SupabaseService>();
    try {
      final results = await Future.wait([
        svc.getPendingHandoffs(),
        svc.getHandoffCustomers(),
        svc.getOrphanedHandoffs(),
      ]);

      final queueData = results[0] as List<Map<String, dynamic>>;
      final activeCustomers = results[1] as List<Customer>;
      final rescuedData = results[2] as List<Map<String, dynamic>>;

      if (mounted) {
        setState(() {
          final List<_QueueItem> list = queueData.map((e) => _QueueItem.fromJson(e)).toList();

          final existingCustIds = list.map((e) => e.customerId).toSet();
          
          // Add flagged customers
          for (var c in activeCustomers) {
            if (!existingCustIds.contains(c.id)) {
              list.add(_QueueItem(
                id: 'legacy-${c.id}',
                customerId: c.id,
                customerName: c.name,
                customerPhone: c.phoneNumber,
                reason: 'Manual handoff - Priority attention needed',
                createdAt: c.lastActive,
              ));
              existingCustIds.add(c.id);
            }
          }

          // Add rescued orphaned handoffs from chat
          for (var r in rescuedData) {
            if (!existingCustIds.contains(r['customer_id'])) {
              list.add(_QueueItem(
                id: r['id'],
                customerId: r['customer_id'],
                customerName: r['customers']['name'],
                customerPhone: r['customers']['phone_number'],
                reason: r['reason'],
                createdAt: DateTime.parse(r['created_at']),
              ));
              existingCustIds.add(r['customer_id']);
            }
          }

          list.sort((a, b) => b.createdAt.compareTo(a.createdAt));
          _queue = list;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      _buildHeader(),

      Expanded(
        child: _isLoading
            ? const Center(
                child: CircularProgressIndicator(color: AppColors.primary, strokeWidth: 2))
            : _queue.isEmpty
                ? _buildEmptyState()
                : RefreshIndicator(
                    onRefresh: _fetch,
                    color: AppColors.primary,
                    child: ListView.builder(
                      padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
                      itemCount: _queue.length,
                      itemBuilder: (_, i) {
                        return _buildHandoffCard(_queue[i]);
                      },
                    ),
                  ),
      ),
    ]);
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
      decoration: BoxDecoration(
        color: AppColors.bg,
        border: Border(bottom: BorderSide(color: AppColors.border, width: 0.5)),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          _badge('LIVE SYNC + RESCUE', AppColors.primary),
          const SizedBox(width: 10),
          Text('${_queue.length} students waiting',
              style: GoogleFonts.plusJakartaSans(
                  fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.textMuted)),
        ]),
        const SizedBox(height: 8),
        Text('Human Attention Pipeline',
            style: GoogleFonts.plusJakartaSans(
                fontSize: 18, fontWeight: FontWeight.w800, color: AppColors.textPri)),
      ]),
    );
  }

  Widget _buildHandoffCard(_QueueItem item) {
    bool isManual = item.id.startsWith('legacy-');
    bool isRescued = item.id.startsWith('rescue-');
    
    Color accentColor = isRescued ? AppColors.sky : (isManual ? AppColors.peach : AppColors.primary);
    
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: accentColor.withOpacity(0.3)),
        boxShadow: [
          BoxShadow(
              color: accentColor.withOpacity(0.05),
              blurRadius: 15,
              offset: const Offset(0, 8)),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: Column(children: [
          Container(height: 4, width: double.infinity, color: accentColor),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                _avatar(item.customerName, isManual, isRescued),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(item.customerName,
                        style: GoogleFonts.plusJakartaSans(
                            fontSize: 15, fontWeight: FontWeight.w800, color: AppColors.textPri)),
                    Text(item.customerPhone,
                        style: GoogleFonts.plusJakartaSans(fontSize: 11, color: AppColors.textSec)),
                  ]),
                ),
                _timeBadge(_timeAgo(item.createdAt)),
              ]),
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.surface2,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Icon(isRescued ? Icons.history_rounded : (isManual ? Icons.flag_rounded : Icons.info_outline_rounded), size: 16, color: accentColor),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(isRescued ? 'CHAT LOG RECOVERY' : (isManual ? 'MANUAL HANDOFF' : 'REASON'), style: GoogleFonts.plusJakartaSans(fontSize: 9, fontWeight: FontWeight.w800, color: AppColors.textMuted, letterSpacing: 0.8)),
                      const SizedBox(height: 4),
                      Text(item.reason, style: GoogleFonts.plusJakartaSans(fontSize: 13, color: AppColors.textPri, fontWeight: FontWeight.w600)),
                    ]),
                  ),
                ]),
              ),
              const SizedBox(height: 20),
              Row(children: [
                _actionBtn(Icons.check_circle_rounded, 'Mark Resolved', AppColors.primary, () async {
                  await context.read<SupabaseService>().resolveHandoff(item.id, item.customerId);
                  _fetch();
                }),
                const SizedBox(width: 10),
                _actionBtn(Icons.person_rounded, 'View Profile', AppColors.textMuted, () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => CustomerProfileScreen(customerId: item.customerId)));
                }),
              ]),
            ]),
          ),
        ]),
      ),
    );
  }

  Widget _avatar(String name, bool isManual, bool isRescued) => Container(
        width: 44,
        height: 44,
        decoration: BoxDecoration(
          color: isRescued ? AppColors.sky.withOpacity(0.1) : (isManual ? AppColors.peach.withOpacity(0.1) : AppColors.primaryDim), 
          borderRadius: BorderRadius.circular(14)
        ),
        child: Center(
            child: Text(name[0].toUpperCase(),
                style: GoogleFonts.plusJakartaSans(
                    fontSize: 18, 
                    color: isRescued ? AppColors.sky : (isManual ? AppColors.peach : AppColors.primary), 
                    fontWeight: FontWeight.w800))),
      );

  Widget _badge(String label, Color color) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(6)),
        child: Text(label, style: GoogleFonts.plusJakartaSans(fontSize: 9, fontWeight: FontWeight.w800, color: color, letterSpacing: 0.5)),
      );

  Widget _timeBadge(String time) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    decoration: BoxDecoration(color: AppColors.surface2, borderRadius: BorderRadius.circular(8)),
    child: Text(time, style: GoogleFonts.plusJakartaSans(fontSize: 10, fontWeight: FontWeight.w700, color: AppColors.textSec)),
  );

  Widget _actionBtn(IconData icon, String label, Color color, VoidCallback onTap) => Expanded(
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 10),
            decoration: BoxDecoration(
                color: color.withOpacity(0.08),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: color.withOpacity(0.2))),
            child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              Icon(icon, size: 16, color: color),
              const SizedBox(width: 8),
              Text(label,
                  style: GoogleFonts.plusJakartaSans(
                      fontSize: 12, fontWeight: FontWeight.w700, color: color)),
            ]),
          ),
        ),
      );

  Widget _buildEmptyState() => Center(
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Container(
          width: 80,
          height: 80,
          decoration: BoxDecoration(color: AppColors.primaryDim, shape: BoxShape.circle),
          child: const Icon(Icons.check_circle_outline_rounded, size: 36, color: AppColors.primary),
        ),
        const SizedBox(height: 20),
        Text('All caught up!',
            style: GoogleFonts.plusJakartaSans(
                color: AppColors.textPri, fontSize: 18, fontWeight: FontWeight.w800)),
        const SizedBox(height: 6),
        Text('No pending handoffs found',
            style: GoogleFonts.plusJakartaSans(color: AppColors.textSec, fontSize: 13)),
      ]));

  String _timeAgo(DateTime dt) {
    final d = DateTime.now().difference(dt);
    if (d.inMinutes < 60) return '${d.inMinutes}m ago';
    if (d.inHours < 24) return '${d.inHours}h ago';
    return DateFormat('dd MMM').format(dt);
  }
}

class _QueueItem {
  final String id;
  final String customerId;
  final String customerName;
  final String customerPhone;
  final String reason;
  final DateTime createdAt;

  _QueueItem({
    required this.id,
    required this.customerId,
    required this.customerName,
    required this.customerPhone,
    required this.reason,
    required this.createdAt,
  });

  factory _QueueItem.fromJson(Map<String, dynamic> json) {
    final cust = json['customers'] as Map<String, dynamic>? ?? {};
    return _QueueItem(
      id: json['id'],
      customerId: json['customer_id'],
      customerName: cust['name'] ?? 'Unknown',
      customerPhone: cust['phone_number'] ?? '-',
      reason: json['reason'] ?? 'Attention Required',
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}
