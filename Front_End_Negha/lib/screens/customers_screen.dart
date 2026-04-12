import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../models/customer.dart';
import '../services/supabase_service.dart';
import 'customer_profile_screen.dart';

class CustomersScreen extends StatefulWidget {
  const CustomersScreen({super.key});
  @override
  State<CustomersScreen> createState() => _CustomersScreenState();
}

class _CustomersScreenState extends State<CustomersScreen> {
  List<Customer> _all = [], _filtered = [];
  bool _isLoading = true;
  String _search = '';
  String _catFilter = 'All';
  String _countryFilter = 'All';
  String _riskFilter = 'All';
  final _cats = ['All', 'Champion', 'Potential', 'At Risk'];
  final _countries = ['All', 'Germany', 'France', 'Netherlands'];
  final _risks = ['All', 'High', 'Medium', 'Low'];

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    final svc = context.read<SupabaseService>();
    try {
      final list = await svc.getAllCustomers();
      if (mounted) {
        setState(() {
          _all = list;
          _applyFilters();
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _applyFilters() {
    _filtered = _all.where((c) {
      final matchSearch = _search.isEmpty ||
          c.name.toLowerCase().contains(_search.toLowerCase()) ||
          c.phoneNumber.contains(_search);
      final matchCat = _catFilter == 'All' || c.calculatedCategory == _catFilter;
      final matchCountry = _countryFilter == 'All' || c.preferredCountry == _countryFilter;
      final matchRisk = _riskFilter == 'All' || c.riskLevel.toLowerCase() == _riskFilter.toLowerCase();
      return matchSearch && matchCat && matchCountry && matchRisk;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      // Modern Search & Header
      _buildHeader(),

      // Body List
      Expanded(
        child: _isLoading
            ? const Center(
                child: CircularProgressIndicator(color: AppColors.primary, strokeWidth: 2))
            : _filtered.isEmpty
                ? _buildEmptyState()
                : RefreshIndicator(
                    onRefresh: _fetch,
                    color: AppColors.primary,
                    child: ListView.builder(
                      padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                      itemCount: _filtered.length,
                      itemBuilder: (_, i) {
                        final c = _filtered[i];
                        return _buildStudentCard(c);
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
        // Search Bar
        TextField(
          decoration: InputDecoration(
            hintText: 'Find a student...',
            hintStyle: GoogleFonts.plusJakartaSans(color: AppColors.textMuted, fontSize: 13),
            prefixIcon: const Icon(Icons.search_rounded, color: AppColors.primary, size: 20),
            filled: true,
            fillColor: AppColors.surface2,
            border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
            contentPadding: const EdgeInsets.symmetric(vertical: 0),
          ),
          style: GoogleFonts.plusJakartaSans(
              color: AppColors.textPri, fontSize: 13, fontWeight: FontWeight.w600),
          onChanged: (v) {
            setState(() {
              _search = v;
              _applyFilters();
            });
          },
        ),
        const SizedBox(height: 16),
        // Filter Row
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          physics: const BouncingScrollPhysics(),
          child: Row(children: [
            _filterChip('Category', _catFilter, _cats, (v) => setState(() { _catFilter = v; _applyFilters(); })),
            const SizedBox(width: 10),
            _filterChip('Country', _countryFilter, _countries, (v) => setState(() { _countryFilter = v; _applyFilters(); })),
            const SizedBox(width: 10),
            _filterChip('Risk', _riskFilter, _risks, (v) => setState(() { _riskFilter = v; _applyFilters(); })),
            const SizedBox(width: 14),
            Text('${_filtered.length} Results', 
              style: GoogleFonts.plusJakartaSans(fontSize: 11, fontWeight: FontWeight.w800, color: AppColors.textMuted)),
          ]),
        ),
      ]),
    );
  }

  Widget _filterChip(String label, String current, List<String> options, ValueChanged<String> onChanged) {
    final isActive = current != 'All';
    return PopupMenuButton<String>(
      tooltip: 'Filter by $label',
      onSelected: onChanged,
      itemBuilder: (context) => options.map((o) => PopupMenuItem(value: o, child: Text(o, style: GoogleFonts.plusJakartaSans(fontSize: 13)))).toList(),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isActive ? AppColors.primary : AppColors.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: isActive ? AppColors.primary : AppColors.border),
          boxShadow: isActive ? [BoxShadow(color: AppColors.primary.withOpacity(0.2), blurRadius: 8, offset: const Offset(0, 2))] : null,
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Text(isActive ? current : label,
              style: GoogleFonts.plusJakartaSans(
                  fontSize: 11, fontWeight: FontWeight.w700, 
                  color: isActive ? Colors.white : AppColors.textSec)),
          const SizedBox(width: 4),
          Icon(Icons.keyboard_arrow_down_rounded, 
            size: 14, color: isActive ? Colors.white : AppColors.textMuted),
        ]),
      ),
    );
  }

  Widget _buildStudentCard(Customer c) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => CustomerProfileScreen(customerId: c.id))),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(children: [
            Row(children: [
              _avatar(c),
              const SizedBox(width: 12),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(c.name, style: GoogleFonts.plusJakartaSans(
                    fontWeight: FontWeight.w800, fontSize: 15, color: AppColors.textPri, letterSpacing: -0.2)),
                Text(c.phoneNumber, style: GoogleFonts.plusJakartaSans(fontSize: 11, color: AppColors.textSec)),
              ])),
              _churnBadge(c.churnScore),
            ]),
            const SizedBox(height: 14),
            Divider(color: AppColors.border, height: 1),
            const SizedBox(height: 14),
            Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              _infoItem('Preference', '${c.countryFlag} ${c.preferredCountry ?? 'Any'}'),
              _infoItem('Category', c.calculatedCategory),
              _infoItem('Risk', c.riskLevel.toUpperCase()),
              // Status indicators
              Row(children: [
                 if (c.isHandoffActive) _statusIcon(Icons.warning_amber_rounded, AppColors.peach),
                 if (c.appointmentRequested) _statusIcon(Icons.calendar_month_rounded, AppColors.lavender),
                 const Icon(Icons.chevron_right_rounded, color: AppColors.textMuted, size: 20),
              ]),
            ]),
          ]),
        ),
      ),
    );
  }

  Widget _avatar(Customer c) => Container(
    width: 40, height: 40,
    decoration: BoxDecoration(
      gradient: LinearGradient(colors: [AppColors.primary, AppColors.primary.withOpacity(0.7)]),
      borderRadius: BorderRadius.circular(12),
    ),
    child: Center(child: Text(
      c.name.isNotEmpty ? c.name[0].toUpperCase() : '?',
      style: GoogleFonts.plusJakartaSans(fontSize: 16, color: Colors.white, fontWeight: FontWeight.w800),
    )),
  );

  Widget _infoItem(String label, String value) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(label, style: GoogleFonts.plusJakartaSans(fontSize: 9, color: AppColors.textMuted, fontWeight: FontWeight.w600)),
      const SizedBox(height: 2),
      Text(value, style: GoogleFonts.plusJakartaSans(fontSize: 11, color: AppColors.textSec, fontWeight: FontWeight.w700)),
    ],
  );

  Widget _statusIcon(IconData icon, Color color) => Container(
    margin: const EdgeInsets.only(right: 6),
    padding: const EdgeInsets.all(4),
    decoration: BoxDecoration(color: color.withOpacity(0.1), shape: BoxShape.circle),
    child: Icon(icon, size: 12, color: color),
  );

  Widget _churnBadge(double score) {
    final color = score > 0.7 ? AppColors.peach : (score > 0.4 ? AppColors.sand : AppColors.sage);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
      child: Text('${(score * 100).round()}% Risk', 
        style: GoogleFonts.plusJakartaSans(fontSize: 10, fontWeight: FontWeight.w800, color: color)),
    );
  }

  Widget _buildEmptyState() => Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
    Icon(Icons.search_off_rounded, size: 48, color: AppColors.textMuted),
    const SizedBox(height: 16),
    Text('No students found', style: GoogleFonts.plusJakartaSans(color: AppColors.textSec, fontWeight: FontWeight.w700)),
  ]));
}
