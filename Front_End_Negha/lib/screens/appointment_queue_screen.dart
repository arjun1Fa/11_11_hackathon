import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../models/customer.dart';
import '../services/supabase_service.dart';
import 'customer_profile_screen.dart';

class AppointmentQueueScreen extends StatefulWidget {
  const AppointmentQueueScreen({super.key});
  @override
  State<AppointmentQueueScreen> createState() => _AppointmentQueueScreenState();
}

class _AppointmentQueueScreenState extends State<AppointmentQueueScreen> {
  List<Customer> _customers = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    final svc = context.read<SupabaseService>();
    try {
      final list = await svc.getAppointmentCustomers();
      if (mounted) {
        setState(() {
          _customers = list;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _markDone(Customer c) async {
    try {
      await context.read<SupabaseService>().updateAppointmentRequested(c.id, false);
      if (mounted) {
        setState(() => _customers.removeWhere((x) => x.id == c.id));
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('✅ ${c.name} appointment marked done'),
          behavior: SnackBarBehavior.floating,
          backgroundColor: AppColors.sage,
        ));
      }
    } catch (_) {}
  }

  Future<void> _resetAll() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Text('Reset Appointments?',
            style: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w800, fontSize: 18)),
        content: Text('This will clear ${_customers.length} requests. Continue?',
            style: GoogleFonts.plusJakartaSans(fontSize: 14)),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: Text('Cancel', style: GoogleFonts.plusJakartaSans(color: AppColors.textSec))),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.lavender,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Reset All'),
          ),
        ],
      ),
    );
    if (confirm == true) {
      await context.read<SupabaseService>().resetAllAppointments();
      _fetch();
    }
  }

  void _sendBookingLink(Customer c) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        title: Text('Send Booking Link',
            style: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w800, fontSize: 20)),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          Text('Sending to ${c.name}',
              style: GoogleFonts.plusJakartaSans(fontSize: 13, color: AppColors.textSec)),
          const SizedBox(height: 20),
          TextField(
            controller: controller,
            decoration: InputDecoration(
              hintText: 'Calendly / Booking URL...',
              hintStyle: GoogleFonts.plusJakartaSans(fontSize: 13),
              filled: true,
              fillColor: AppColors.surface2,
              border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
              prefixIcon: const Icon(Icons.link_rounded, size: 18),
            ),
          ),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          Padding(
            padding: const EdgeInsets.only(right: 8, bottom: 8),
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
              onPressed: () {
                Navigator.pop(ctx);
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                  content: Text('📤 Link sent to ${c.name}'),
                  behavior: SnackBarBehavior.floating,
                  backgroundColor: AppColors.primary,
                ));
              },
              child: const Text('Send Link'),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      // Premium Header
      _buildHeader(),

      Expanded(
        child: _isLoading
            ? const Center(
                child: CircularProgressIndicator(color: AppColors.primary, strokeWidth: 2))
            : _customers.isEmpty
                ? _buildEmptyState()
                : RefreshIndicator(
                    onRefresh: _fetch,
                    color: AppColors.primary,
                    child: ListView.builder(
                      padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
                      itemCount: _customers.length,
                      itemBuilder: (_, i) {
                        return _buildAppointmentCard(_customers[i]);
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
      child: Row(children: [
        Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Appointment Queue',
              style: GoogleFonts.plusJakartaSans(
                  fontSize: 16, fontWeight: FontWeight.w800, color: AppColors.textPri)),
          Text('${_customers.length} pending requests',
              style: GoogleFonts.plusJakartaSans(fontSize: 11, color: AppColors.textSec)),
        ]),
        const Spacer(),
        _actionBtnHeader(Icons.restart_alt_rounded, 'Reset Queue', AppColors.lavender, _resetAll),
      ]),
    );
  }

  Widget _buildAppointmentCard(Customer c) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.lavender.withOpacity(0.3)),
        boxShadow: [
          BoxShadow(
              color: AppColors.lavender.withOpacity(0.06),
              blurRadius: 15,
              offset: const Offset(0, 6)),
        ],
      ),
      child: Column(children: [
        Padding(
          padding: const EdgeInsets.all(20),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              _avatar(c),
              const SizedBox(width: 14),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(c.name,
                      style: GoogleFonts.plusJakartaSans(
                          fontSize: 15, fontWeight: FontWeight.w800, color: AppColors.textPri)),
                  Text(c.phoneNumber,
                      style: GoogleFonts.plusJakartaSans(fontSize: 11, color: AppColors.textSec)),
                ]),
              ),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(color: AppColors.lavenderDim, shape: BoxShape.circle),
                child: Icon(Icons.calendar_month_rounded, size: 18, color: AppColors.lavender),
              ),
            ]),
            const SizedBox(height: 16),
            Wrap(spacing: 8, runSpacing: 8, children: [
              _infoBadge('${c.countryFlag} ${c.preferredCountry ?? 'Any'}'),
              if (c.ieltsScore != null) _infoBadge('IELTS ${c.ieltsScore}'),
              _infoBadge(_timeAgo(c.lastActive)),
            ]),
            const SizedBox(height: 20),
            Row(children: [
              _actionBtn(Icons.link_rounded, 'Send Link', AppColors.primary, () => _sendBookingLink(c)),
              const SizedBox(width: 10),
              _actionBtn(Icons.check_circle_rounded, 'Mark Done', AppColors.sage, () => _markDone(c)),
              const SizedBox(width: 10),
              _actionBtn(Icons.person_rounded, 'Profile', AppColors.lavender, () {
                Navigator.push(context, MaterialPageRoute(builder: (_) => CustomerProfileScreen(customerId: c.id)));
              }),
            ]),
          ]),
        ),
      ]),
    );
  }

  Widget _avatar(Customer c) => Container(
        width: 44,
        height: 44,
        decoration: BoxDecoration(color: AppColors.lavenderDim, borderRadius: BorderRadius.circular(14)),
        child: Center(
            child: Text(c.name.isNotEmpty ? c.name[0].toUpperCase() : '?',
                style: GoogleFonts.plusJakartaSans(
                    fontSize: 18, color: AppColors.lavender, fontWeight: FontWeight.w800))),
      );

  Widget _infoBadge(String text) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(color: AppColors.surface2, borderRadius: BorderRadius.circular(8)),
        child: Text(text,
            style: GoogleFonts.plusJakartaSans(
                fontSize: 10, fontWeight: FontWeight.w700, color: AppColors.textSec)),
      );

  Widget _actionBtnHeader(IconData icon, String label, Color color, VoidCallback onTap) => InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
          child: Row(children: [
            Icon(icon, size: 14, color: color),
            const SizedBox(width: 6),
            Text(label,
                style: GoogleFonts.plusJakartaSans(
                    fontSize: 11, fontWeight: FontWeight.w700, color: color)),
          ]),
        ),
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
              const SizedBox(width: 6),
              Text(label,
                  style: GoogleFonts.plusJakartaSans(
                      fontSize: 11, fontWeight: FontWeight.w700, color: color)),
            ]),
          ),
        ),
      );

  Widget _buildEmptyState() => Center(
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Container(
          width: 80,
          height: 80,
          decoration: BoxDecoration(color: AppColors.lavenderDim, shape: BoxShape.circle),
          child: const Icon(Icons.event_available_rounded, size: 36, color: AppColors.lavender),
        ),
        const SizedBox(height: 20),
        Text('No Appointments',
            style: GoogleFonts.plusJakartaSans(
                color: AppColors.textPri, fontSize: 18, fontWeight: FontWeight.w800)),
        const SizedBox(height: 6),
        Text('Queue is empty',
            style: GoogleFonts.plusJakartaSans(color: AppColors.textSec, fontSize: 13)),
      ]));

  String _timeAgo(DateTime dt) {
    final d = DateTime.now().difference(dt);
    if (d.inMinutes < 60) return '${d.inMinutes}m ago';
    if (d.inHours < 24) return '${d.inHours}h ago';
    return DateFormat('dd MMM').format(dt);
  }
}
