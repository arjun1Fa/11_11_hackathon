import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../models/customer.dart';
import '../models/enquiry_event.dart';
import '../models/conversation.dart';
import '../services/supabase_service.dart';
import 'conversation_detail_screen.dart';

class CustomerProfileScreen extends StatefulWidget {
  final String customerId;
  const CustomerProfileScreen({super.key, required this.customerId});
  @override
  State<CustomerProfileScreen> createState() => _CustomerProfileScreenState();
}

class _CustomerProfileScreenState extends State<CustomerProfileScreen> {
  Customer? _customer;
  List<EnquiryEvent> _enquiries = [];
  List<Conversation> _conversations = [];
  bool _isLoading = true;

  @override
  void initState() { super.initState(); _fetchAll(); }

  Future<void> _fetchAll() async {
    final svc = context.read<SupabaseService>();
    try {
      final customer = await svc.getCustomerById(widget.customerId);
      if (customer == null) { setState(() => _isLoading = false); return; }
      final results = await Future.wait([
        svc.getEnquiryEventsForCustomer(widget.customerId),
        svc.getConversationsForCustomer(widget.customerId),
      ]);
      if (mounted) setState(() {
        _customer = customer;
        _enquiries = results[0] as List<EnquiryEvent>;
        _conversations = (results[1] as List<Conversation>).reversed.take(10).toList();
        _isLoading = false;
      });
    } catch (e) { if (mounted) setState(() => _isLoading = false); }
  }

  Future<void> _toggleField(String field, bool current) async {
    try {
      await context.read<SupabaseService>().updateCustomerField(
          widget.customerId, field, !current);
      _fetchAll();
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('Updated $field'),
        backgroundColor: AppColors.primary));
    } catch (_) {}
  }

  Future<void> _editField(String label, String field, String? currentValue) async {
    final controller = TextEditingController(text: currentValue);
    final result = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text('Edit $label', style: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w700)),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: InputDecoration(
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
            hintText: 'Enter new value...',
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, controller.text),
            child: const Text('Save'),
          ),
        ],
      ),
    );
    if (result != null && result.isNotEmpty) {
      try {
        dynamic value = result;
        if (field == 'ielts_score') value = double.tryParse(result) ?? result;
        if (field == 'churn_score') value = double.tryParse(result) ?? result;
        await context.read<SupabaseService>().updateCustomerField(widget.customerId, field, value);
        _fetchAll();
      } catch (_) {}
    }
  }

  Widget _riskBadge(String risk) {
    Color color;
    switch (risk.toLowerCase()) {
      case 'high': color = AppColors.peach; break;
      case 'medium': color = AppColors.sand; break;
      default: color = AppColors.sage;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withOpacity(0.4)),
      ),
      child: Text(risk.toUpperCase(), style: GoogleFonts.plusJakartaSans(
          fontSize: 10, fontWeight: FontWeight.w800, color: color)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_customer != null ? '${_customer!.countryFlag} ${_customer!.name}' : 'Student',
          style: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w700)),
        actions: [
          if (_customer != null) IconButton(
            icon: const Icon(Icons.chat_bubble_outline, size: 20),
            onPressed: () => Navigator.push(context, MaterialPageRoute(
              builder: (_) => ConversationDetailScreen(
                customerId: _customer!.id,
                customerName: _customer!.name,
                preferredCountry: _customer!.preferredCountry,
              ),
            )),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.primary, strokeWidth: 2))
          : _customer == null
              ? Center(child: Text('Student not found', style: GoogleFonts.plusJakartaSans(color: AppColors.textMuted)))
              : RefreshIndicator(
                  onRefresh: _fetchAll, color: AppColors.primary,
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      _sec('IDENTITY'), _identityCard(),
                      const SizedBox(height: 16),
                      _sec('TOGGLE CONTROLS'), _togglesCard(),
                      const SizedBox(height: 16),
                      _sec('STUDY ABROAD PROFILE'), _profileCard(),
                      const SizedBox(height: 16),
                      _sec('RISK ASSESSMENT'), _riskCard(),
                      const SizedBox(height: 16),
                      _sec('ENQUIRY HISTORY'), _enquiryCard(),
                      const SizedBox(height: 16),
                      _sec('RECENT MESSAGES'), _messagesCard(),
                      const SizedBox(height: 32),
                    ]),
                  ),
                ),
    );
  }

  Widget _sec(String t) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Text(t, style: GoogleFonts.plusJakartaSans(fontSize: 9, fontWeight: FontWeight.w700,
        color: AppColors.textMuted, letterSpacing: 1.2)));

  Widget _card(Widget child) => Container(
    width: double.infinity, padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(color: AppColors.surface, borderRadius: BorderRadius.circular(14),
      border: Border.all(color: AppColors.border),
      boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 8, offset: const Offset(0, 2))]),
    child: child);

  Widget _editableRow(String label, String? value, String field) => InkWell(
    onTap: () => _editField(label, field, value),
    child: Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        SizedBox(width: 110, child: Text(label, style: GoogleFonts.plusJakartaSans(fontSize: 12, color: AppColors.textSec))),
        Expanded(child: Text(value ?? '-', style: GoogleFonts.plusJakartaSans(fontSize: 12,
            color: AppColors.textPri, fontWeight: FontWeight.w500))),
        Icon(Icons.edit_outlined, size: 14, color: AppColors.textMuted),
      ])),
  );

  Widget _row(String label, String? value) => Padding(
    padding: const EdgeInsets.only(bottom: 6),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      SizedBox(width: 110, child: Text(label, style: GoogleFonts.plusJakartaSans(fontSize: 12, color: AppColors.textSec))),
      Expanded(child: Text(value ?? '-', style: GoogleFonts.plusJakartaSans(fontSize: 12,
          color: AppColors.textPri, fontWeight: FontWeight.w500))),
    ]));

  Widget _identityCard() {
    final c = _customer!;
    return _card(Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        Container(width: 44, height: 44, decoration: BoxDecoration(
            color: AppColors.primaryDim, borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.primary.withOpacity(0.3))),
          child: Center(child: Text(c.name.isNotEmpty ? c.name[0].toUpperCase() : '?',
            style: GoogleFonts.plusJakartaSans(fontSize: 20, color: AppColors.primary, fontWeight: FontWeight.w700)))),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(c.name, style: GoogleFonts.plusJakartaSans(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.textPri)),
          Text('${c.phoneNumber} • ${c.channel}', style: GoogleFonts.plusJakartaSans(fontSize: 12, color: AppColors.textSec)),
        ])),
        _riskBadge(c.riskLevel),
      ]),
      const SizedBox(height: 12),
      _editableRow('Name', c.name, 'name'),
      _row('Channel', c.channel),
      _row('Member Since', DateFormat('dd MMM yyyy').format(c.createdAt)),
    ]));
  }

  Widget _togglesCard() {
    final c = _customer!;
    return _card(Column(children: [
      _toggleRow('Human Handoff Active', c.isHandoffActive, 'is_handoff_active', AppColors.peach),
      const SizedBox(height: 8),
      _toggleRow('Appointment Requested', c.appointmentRequested, 'appointment_requested', AppColors.lavender),
    ]));
  }

  Widget _toggleRow(String label, bool value, String field, Color color) => Row(
    children: [
      Icon(value ? Icons.toggle_on : Icons.toggle_off_outlined,
          size: 32, color: value ? color : AppColors.textMuted),
      const SizedBox(width: 10),
      Expanded(child: Text(label, style: GoogleFonts.plusJakartaSans(
          fontSize: 13, color: AppColors.textPri, fontWeight: FontWeight.w600))),
      Switch(
        value: value,
        activeColor: color,
        onChanged: (_) => _toggleField(field, value),
      ),
    ],
  );

  Widget _profileCard() {
    final c = _customer!;
    return _card(Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _editableRow('Country', c.preferredCountry, 'preferred_country'),
      _editableRow('Education', c.educationLevel, 'education_level'),
      _editableRow('Field of Study', c.fieldOfStudy, 'field_of_study'),
      _editableRow('IELTS Score', c.ieltsScore?.toString(), 'ielts_score'),
      _editableRow('Budget', c.budgetRange, 'budget_range'),
      _row('Language', c.language.toUpperCase()),
      _row('Tone', c.tonePreference),
      _row('Days Inactive', '${c.daysInactive}'),
    ]));
  }

  Widget _riskCard() {
    final c = _customer!;
    return _card(Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        Expanded(child: Text('Churn Score', style: GoogleFonts.plusJakartaSans(
            fontSize: 12, color: AppColors.textSec))),
        Text('${(c.churnScore * 100).round()}%', style: GoogleFonts.plusJakartaSans(
            fontSize: 14, fontWeight: FontWeight.w800,
            color: c.churnScore > 0.7 ? AppColors.peach : c.churnScore > 0.4 ? AppColors.sand : AppColors.sage)),
      ]),
      const SizedBox(height: 8),
      ClipRRect(
        borderRadius: BorderRadius.circular(4),
        child: LinearProgressIndicator(
          value: c.churnScore,
          backgroundColor: AppColors.surface2,
          color: c.churnScore > 0.7 ? AppColors.peach : c.churnScore > 0.4 ? AppColors.sand : AppColors.sage,
          minHeight: 8,
        ),
      ),
      const SizedBox(height: 10),
      Row(children: [
        Text('Category: ', style: GoogleFonts.plusJakartaSans(fontSize: 12, color: AppColors.textSec)),
        _riskBadge(c.calculatedCategory),
        const SizedBox(width: 8),
        Text('Risk Level: ', style: GoogleFonts.plusJakartaSans(fontSize: 12, color: AppColors.textSec)),
        _riskBadge(c.riskLevel),
      ]),
    ]));
  }

  Widget _enquiryCard() => _card(_enquiries.isEmpty
    ? Text('No enquiries', style: GoogleFonts.plusJakartaSans(color: AppColors.textMuted, fontSize: 12))
    : Column(children: _enquiries.map((e) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Row(children: [
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('${e.country ?? '-'} / ${e.packageId ?? '-'}', style: GoogleFonts.plusJakartaSans(
                fontWeight: FontWeight.w600, fontSize: 12, color: AppColors.textPri)),
            Text(DateFormat('dd MMM yyyy').format(e.createdAt), style: GoogleFonts.plusJakartaSans(
                fontSize: 10, color: AppColors.textMuted)),
          ])),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(color: AppColors.surface2,
                borderRadius: BorderRadius.circular(4), border: Border.all(color: AppColors.border)),
            child: Text(e.status, style: GoogleFonts.plusJakartaSans(fontSize: 10,
                color: AppColors.textSec, fontWeight: FontWeight.w600)),
          ),
        ]),
      )).toList()));

  Widget _messagesCard() => _card(_conversations.isEmpty
    ? Text('No messages', style: GoogleFonts.plusJakartaSans(color: AppColors.textMuted, fontSize: 12))
    : Column(children: _conversations.map((c) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Row(children: [
          Icon(c.direction == 'inbound' ? Icons.arrow_downward : Icons.arrow_upward,
              size: 12, color: c.direction == 'inbound' ? AppColors.primary : AppColors.sage),
          const SizedBox(width: 8),
          Expanded(child: Text(
            c.messageText.length > 60 ? '${c.messageText.substring(0, 60)}...' : c.messageText,
            style: GoogleFonts.plusJakartaSans(fontSize: 11, color: AppColors.textSec))),
          Text(DateFormat('HH:mm').format(c.timestamp),
            style: GoogleFonts.plusJakartaSans(fontSize: 9, color: AppColors.textMuted)),
        ]),
      )).toList()));
}
