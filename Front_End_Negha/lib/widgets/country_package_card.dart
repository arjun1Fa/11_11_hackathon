import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../main.dart';
import '../models/package.dart';

class CountryPackageCard extends StatefulWidget {
  final StudyAbroadPackage package;
  const CountryPackageCard({super.key, required this.package});

  @override
  State<CountryPackageCard> createState() => _CountryPackageCardState();
}

class _CountryPackageCardState extends State<CountryPackageCard> {
  bool _isExpanded = false;

  // Initial mappings for the 4 display slots
  final Map<int, String> _fieldMappings = {
    0: 'Budget',
    1: 'Duration',
    2: 'Intake Months',
    3: 'Eligibility',
  };

  final List<String> _availableFields = [
    'Budget', 'Living Cost', 'Duration', 'Intake Months', 
    'Eligibility', 'Visa Support', 'Scholarships', 'Overview',
    'Universities', 'Services Included'
  ];

  @override
  Widget build(BuildContext context) {
    final package = widget.package;
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.lavender.withOpacity(0.3), width: 1.5),
        boxShadow: [
          BoxShadow(color: AppColors.lavender.withOpacity(0.05), blurRadius: 15, offset: const Offset(0, 0)),
          BoxShadow(color: Colors.black.withOpacity(0.4), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header (Collapsible trigger)
          GestureDetector(
            onTap: () => setState(() => _isExpanded = !_isExpanded),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                color: AppColors.surface2,
                borderRadius: BorderRadius.vertical(
                  top: const Radius.circular(16),
                  bottom: Radius.circular(_isExpanded ? 0 : 16),
                ),
                border: Border(bottom: BorderSide(
                  color: _isExpanded ? AppColors.lavender.withOpacity(0.2) : Colors.transparent, width: 1.5)),
              ),
              child: Row(
                children: [
                  Text(package.countryFlag, style: const TextStyle(fontSize: 24)),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(package.packageName,
                          style: GoogleFonts.plusJakartaSans(fontSize: 14,
                              fontWeight: FontWeight.w700, color: AppColors.textPri)),
                        Text(package.country,
                          style: GoogleFonts.plusJakartaSans(fontSize: 11, color: AppColors.textSec)),
                      ],
                    ),
                  ),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppColors.primaryDim,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text('${package.eligibleStudentsCount} students',
                          style: GoogleFonts.plusJakartaSans(fontSize: 10, color: AppColors.primary,
                              fontWeight: FontWeight.w600)),
                      ),
                      const SizedBox(width: 8),
                      Icon(
                        _isExpanded ? Icons.expand_less : Icons.expand_more,
                        size: 18, color: AppColors.textMuted,
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          // Details (Expansion Content)
          AnimatedCrossFade(
            firstChild: const SizedBox(width: double.infinity),
            secondChild: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // High-level Metrics (mapped via dropdowns)
                  Row(
                    children: [
                      Expanded(child: _dynamicInfoTile(0, Icons.payments_outlined)),
                      const SizedBox(width: 8),
                      Expanded(child: _dynamicInfoTile(1, Icons.schedule_outlined)),
                    ],
                  ),
                  const SizedBox(height: 12),
                  // Detailed Rows (mapped via dropdowns)
                  _dynamicInfoRow(2),
                  _dynamicInfoRow(3),
                  
                  const SizedBox(height: 12),
                  Text('TOP UNIVERSITIES',
                    style: GoogleFonts.plusJakartaSans(fontSize: 9, color: AppColors.textMuted,
                        fontWeight: FontWeight.w800, letterSpacing: 1)),
                  const SizedBox(height: 6),
                  ...package.universities.take(3).map((u) => Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Row(
                      children: [
                        Container(width: 4, height: 4,
                          decoration: const BoxDecoration(
                              color: AppColors.primary, shape: BoxShape.circle)),
                        const SizedBox(width: 8),
                        Expanded(child: Text(u,
                          style: GoogleFonts.plusJakartaSans(fontSize: 11, color: AppColors.textSec))),
                      ],
                    ),
                  )),
                ],
              ),
            ),
            crossFadeState: _isExpanded ? CrossFadeState.showSecond : CrossFadeState.showFirst,
            duration: const Duration(milliseconds: 300),
          ),
        ],
      ),
    );
  }

  Widget _dynamicInfoTile(int index, IconData icon) {
    final field = _fieldMappings[index] ?? 'Empty';
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppColors.surface2,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border, width: 1.0),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.2), blurRadius: 6, offset: const Offset(0, 2))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Icon(icon, size: 12, color: AppColors.primary),
              const SizedBox(width: 4),
              Expanded(child: _mappingDropdown(index)),
            ],
          ),
          const SizedBox(height: 6),
          Text(widget.package.getValueByField(field), 
            style: GoogleFonts.plusJakartaSans(fontSize: 11,
              color: AppColors.textPri, fontWeight: FontWeight.w600),
            maxLines: 2, overflow: TextOverflow.ellipsis),
        ],
      ),
    );
  }

  Widget _dynamicInfoRow(int index) {
    final field = _fieldMappings[index] ?? 'Empty';
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          SizedBox(width: 100, child: _mappingDropdown(index)),
          const SizedBox(width: 12),
          Expanded(child: Text(widget.package.getValueByField(field),
            style: GoogleFonts.plusJakartaSans(fontSize: 11, color: AppColors.textPri,
                fontWeight: FontWeight.w600))),
        ],
      ),
    );
  }

  Widget _mappingDropdown(int index) {
    return DropdownButtonHideUnderline(
      child: DropdownButton<String>(
        isExpanded: true,
        isDense: true,
        value: _fieldMappings[index],
        icon: const Icon(Icons.arrow_drop_down, size: 14, color: AppColors.primary),
        style: GoogleFonts.plusJakartaSans(fontSize: 9, color: AppColors.primary, fontWeight: FontWeight.w800),
        onChanged: (val) => setState(() => _fieldMappings[index] = val!),
        items: _availableFields.map((f) => DropdownMenuItem(
          value: f, child: Text(f.toUpperCase(), overflow: TextOverflow.ellipsis))).toList(),
      ),
    );
  }
}
