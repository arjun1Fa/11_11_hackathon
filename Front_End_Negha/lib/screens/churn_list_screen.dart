import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../models/customer.dart';
import '../services/supabase_service.dart';
import 'customer_profile_screen.dart';

class ChurnListScreen extends StatefulWidget {
  const ChurnListScreen({super.key});
  @override
  State<ChurnListScreen> createState() => _ChurnListScreenState();
}

class _ChurnListScreenState extends State<ChurnListScreen> {
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
      final list = await svc.getChurnRiskCustomers();
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

  @override
  Widget build(BuildContext context) {
    return _isLoading
        ? const Center(child: CircularProgressIndicator(color: AppColors.primary, strokeWidth: 2))
        : _customers.isEmpty
            ? _buildEmptyState()
            : RefreshIndicator(
                onRefresh: _fetch,
                color: AppColors.primary,
                child: ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
                  itemCount: _customers.length,
                  itemBuilder: (_, i) {
                    final c = _customers[i];
                    final isCritical = c.churnScore > 0.85;

                    return Container(
                      margin: const EdgeInsets.only(bottom: 16),
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                            color: isCritical
                                ? AppColors.peach.withOpacity(0.4)
                                : AppColors.border,
                            width: 1.5),
                        boxShadow: [
                          BoxShadow(
                              color: isCritical
                                  ? AppColors.peach.withOpacity(0.12)
                                  : Colors.black.withOpacity(0.05),
                              blurRadius: 20,
                              offset: const Offset(0, 8)),
                        ],
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(20),
                        child: Column(children: [
                          // Top Accent Line
                          if (isCritical)
                            Container(height: 4, width: double.infinity, color: AppColors.peach),

                          Padding(
                            padding: const EdgeInsets.all(20),
                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                    _avatar(c),
                                    const SizedBox(width: 14),
                                    Expanded(
                                        child: Column(
                                            crossAxisAlignment: CrossAxisAlignment.start,
                                            children: [
                                          Text(c.name,
                                              style: GoogleFonts.plusJakartaSans(
                                                  fontWeight: FontWeight.w800,
                                                  fontSize: 16,
                                                  color: AppColors.textPri,
                                                  letterSpacing: -0.4)),
                                          const SizedBox(height: 2),
                                          Text(
                                              '${c.phoneNumber} • ${c.countryFlag} ${c.preferredCountry ?? '-'}',
                                              style: GoogleFonts.plusJakartaSans(
                                                  fontSize: 11, color: AppColors.textSec)),
                                        ])),
                                    _percentage(c.churnScore),
                                  ]),
                                  const SizedBox(height: 22),

                                  // Label & Activity
                                  Row(children: [
                                    Text('CHURN PROBABILITY',
                                        style: GoogleFonts.plusJakartaSans(
                                            fontSize: 9,
                                            fontWeight: FontWeight.w800,
                                            color: AppColors.textMuted,
                                            letterSpacing: 0.8)),
                                    const Spacer(),
                                    _activityBadge(c.daysInactive),
                                  ]),
                                  const SizedBox(height: 10),

                                  // Stylized Heat Bar
                                  _heatBar(c.churnScore),

                                  const SizedBox(height: 20),
                                  _statsRow(c),
                                  const SizedBox(height: 20),

                                  Row(children: [
                                    _actionBtn(Icons.person_outline, 'Open Profile',
                                        AppColors.primary, () {
                                      Navigator.push(
                                          context,
                                          MaterialPageRoute(
                                              builder: (_) =>
                                                  CustomerProfileScreen(customerId: c.id)));
                                    }),
                                    const SizedBox(width: 10),
                                    _actionBtn(Icons.auto_awesome, 'Escalate to AI/Agent',
                                        AppColors.peach, () async {
                                      await context.read<SupabaseService>().createHandoff(
                                          c.id, 'churn_risk_escalation', c.preferredCountry);
                                      if (mounted) {
                                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                                            content: Text('⚠️ ${c.name} escalation sent'),
                                            behavior: SnackBarBehavior.floating,
                                            backgroundColor: AppColors.peach));
                                      }
                                    }),
                                  ]),
                                ]),
                          ),
                        ]),
                      ),
                    );
                  },
                ),
              );
  }

  Widget _avatar(Customer c) => Container(
        width: 44,
        height: 44,
        decoration: BoxDecoration(
          color: AppColors.primaryDim,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Center(
            child: Text(
          c.name.isNotEmpty ? c.name[0].toUpperCase() : '?',
          style: GoogleFonts.plusJakartaSans(
              fontSize: 20, color: AppColors.primary, fontWeight: FontWeight.w800),
        )),
      );

  Widget _percentage(double score) => Column(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Text('${(score * 100).round()}%',
              style: GoogleFonts.outfit(
                  fontSize: 28, fontWeight: FontWeight.w800, color: AppColors.peach, height: 1.0)),
          Text('RISK',
              style: GoogleFonts.plusJakartaSans(
                  fontSize: 9, fontWeight: FontWeight.w800, color: AppColors.peach.withOpacity(0.6))),
        ],
      );

  Widget _heatBar(double score) {
    return Container(
      height: 10,
      width: double.infinity,
      decoration: BoxDecoration(
        color: AppColors.surface2,
        borderRadius: BorderRadius.circular(10),
      ),
      child: FractionallySizedBox(
        alignment: Alignment.centerLeft,
        widthFactor: score,
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(colors: [
              AppColors.peach.withOpacity(0.6),
              AppColors.peach,
            ]),
            borderRadius: BorderRadius.circular(10),
            boxShadow: [
              BoxShadow(color: AppColors.peach.withOpacity(0.3), blurRadius: 4, offset: const Offset(0, 2)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _activityBadge(int days) {
    final color = days > 5 ? AppColors.peach : AppColors.sage;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text('${days}d Inactive',
          style: GoogleFonts.plusJakartaSans(
              fontSize: 10, fontWeight: FontWeight.w700, color: color)),
    );
  }

  Widget _statsRow(Customer c) => Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _statItem('Education', c.educationLevel ?? 'N/A'),
          _statItem('IELTS', c.ieltsScore?.toString() ?? 'N/A'),
          _statItem('Country', c.preferredCountry ?? 'N/A'),
        ],
      );

  Widget _statItem(String label, String value) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label,
              style: GoogleFonts.plusJakartaSans(fontSize: 9, color: AppColors.textMuted)),
          const SizedBox(height: 2),
          Text(value,
              style: GoogleFonts.plusJakartaSans(
                  fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.textPri)),
        ],
      );

  Widget _buildEmptyState() => Center(
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Container(
          width: 80,
          height: 80,
          decoration: BoxDecoration(color: AppColors.sageDim, shape: BoxShape.circle),
          child: const Icon(Icons.favorite_rounded, size: 36, color: AppColors.sage),
        ),
        const SizedBox(height: 20),
        Text('All Healthy!',
            style: GoogleFonts.plusJakartaSans(
                color: AppColors.textPri, fontSize: 20, fontWeight: FontWeight.w800)),
        const SizedBox(height: 6),
        Text('No students at high churn risk',
            style: GoogleFonts.plusJakartaSans(color: AppColors.textSec, fontSize: 13)),
      ]));

  Widget _actionBtn(IconData icon, String label, Color color, VoidCallback onTap) => Expanded(
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 12),
            decoration: BoxDecoration(
              color: color.withOpacity(0.08),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: color.withOpacity(0.2)),
            ),
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
}
