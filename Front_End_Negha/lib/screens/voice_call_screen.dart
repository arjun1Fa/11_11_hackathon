import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../services/supabase_service.dart';

class VoiceCallScreen extends StatefulWidget {
  const VoiceCallScreen({super.key});
  @override
  State<VoiceCallScreen> createState() => _VoiceCallScreenState();
}

class _VoiceCallScreenState extends State<VoiceCallScreen> {
  List<Map<String, dynamic>> _calls = [];
  bool _isLoading = true;
  final Set<String> _completed = {};
  final Set<String> _voicemail = {};

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    final svc = context.read<SupabaseService>();
    try {
      final list = await svc.getVoiceCallConversations();
      if (mounted) {
        setState(() {
          _calls = list;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  String _formatAction(String? action) {
    switch (action) {
      case 'start_call': return 'Immediate Call';
      case 'schedule_followup': return 'Follow-up Call';
      default: return action ?? 'Task';
    }
  }

  @override
  Widget build(BuildContext context) {
    return _isLoading
        ? const Center(child: CircularProgressIndicator(color: AppColors.primary, strokeWidth: 2))
        : _calls.isEmpty
            ? _buildEmptyState()
            : RefreshIndicator(
                onRefresh: _fetch,
                color: AppColors.primary,
                child: ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
                  itemCount: _calls.length,
                  itemBuilder: (_, i) {
                    final call = _calls[i];
                    final cust = call['customers'] as Map<String, dynamic>?;
                    final id = call['id'] as String;
                    final isDone = _completed.contains(id);
                    final isVm = _voicemail.contains(id);

                    return _buildCallCard(id, cust, call, isDone, isVm);
                  },
                ),
              );
  }

  Widget _buildCallCard(String id, Map<String, dynamic>? cust, Map<String, dynamic> call, bool isDone, bool isVm) {
    final statusColor = isDone ? AppColors.sage : (isVm ? AppColors.sand : AppColors.primary);
    final statusLabel = isDone ? 'COMPLETED' : (isVm ? 'VOICEMAIL' : 'PENDING');
    final isActionable = !isDone && !isVm;

    return AnimatedOpacity(
      opacity: isActionable ? 1.0 : 0.6,
      duration: const Duration(milliseconds: 300),
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: isActionable ? AppColors.sand.withOpacity(0.3) : AppColors.border),
          boxShadow: [
            BoxShadow(
              color: isActionable ? AppColors.sand.withOpacity(0.08) : Colors.black.withOpacity(0.02),
              blurRadius: 12, offset: const Offset(0, 4)),
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(20),
          child: Column(children: [
            if (isActionable) Container(height: 4, width: double.infinity, color: AppColors.sand),
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  _avatar(cust?['name'] ?? '?'),
                  const SizedBox(width: 14),
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(cust?['name'] ?? 'Unknown Student', style: GoogleFonts.plusJakartaSans(
                        fontSize: 15, fontWeight: FontWeight.w800, color: AppColors.textPri)),
                    Text(cust?['phone_number'] ?? 'No number', style: GoogleFonts.plusJakartaSans(
                        fontSize: 11, color: AppColors.textSec)),
                  ])),
                  _statusBadge(statusLabel, statusColor),
                ]),
                const SizedBox(height: 20),
                Row(children: [
                  Icon(Icons.auto_awesome_rounded, size: 14, color: AppColors.sand),
                  const SizedBox(width: 8),
                  Text(_formatAction(call['action_taken'] as String?), 
                    style: GoogleFonts.plusJakartaSans(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.textPri)),
                  const Spacer(),
                  if (cust?['preferred_country'] != null) 
                    Text(cust!['preferred_country'], style: GoogleFonts.plusJakartaSans(fontSize: 11, color: AppColors.textMuted)),
                ]),
                const SizedBox(height: 12),
                if (call['intent_label'] != null)
                   Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(color: AppColors.surface2, borderRadius: BorderRadius.circular(8)),
                    child: Text('INTENT: ${call['intent_label']}', style: GoogleFonts.plusJakartaSans(fontSize: 10, fontWeight: FontWeight.w800, color: AppColors.textSec, letterSpacing: 0.5)),
                  ),
                
                if (isActionable) ...[
                  const SizedBox(height: 20),
                  Row(children: [
                    _actionBtn(Icons.check_circle_outline_rounded, 'Completed', AppColors.sage, () => setState(() => _completed.add(id))),
                    const SizedBox(width: 10),
                    _actionBtn(Icons.voicemail_rounded, 'Voicemail', AppColors.sand, () => setState(() => _voicemail.add(id))),
                  ]),
                ],
              ]),
            ),
          ]),
        ),
      ),
    );
  }

  Widget _avatar(String name) => Container(
    width: 44, height: 44,
    decoration: BoxDecoration(color: AppColors.sandDim, borderRadius: BorderRadius.circular(14)),
    child: Center(child: Text(name[0].toUpperCase(), style: GoogleFonts.plusJakartaSans(fontSize: 18, color: AppColors.sand, fontWeight: FontWeight.w800))),
  );

  Widget _statusBadge(String label, Color color) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
    decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(10), border: Border.all(color: color.withOpacity(0.2))),
    child: Text(label, style: GoogleFonts.plusJakartaSans(fontSize: 9, fontWeight: FontWeight.w800, color: color, letterSpacing: 0.5)),
  );

  Widget _actionBtn(IconData icon, String label, Color color, VoidCallback onTap) => Expanded(
    child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(color: color.withOpacity(0.08), borderRadius: BorderRadius.circular(12), border: Border.all(color: color.withOpacity(0.2))),
        child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 8),
          Text(label, style: GoogleFonts.plusJakartaSans(fontSize: 12, fontWeight: FontWeight.w700, color: color)),
        ]),
      ),
    ),
  );

  Widget _buildEmptyState() => Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
    Container(
      width: 80, height: 80,
      decoration: BoxDecoration(color: AppColors.sandDim, shape: BoxShape.circle),
      child: const Icon(Icons.phone_disabled_rounded, size: 36, color: AppColors.sand),
    ),
    const SizedBox(height: 20),
    Text('Inbox Clear', style: GoogleFonts.plusJakartaSans(color: AppColors.textPri, fontSize: 18, fontWeight: FontWeight.w800)),
    const SizedBox(height: 6),
    Text('No pending call requests', style: GoogleFonts.plusJakartaSans(color: AppColors.textSec, fontSize: 13)),
  ]));
}
