import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../main.dart';
import '../models/customer.dart';
import 'category_badge.dart';
import 'churn_score_bar.dart';

class CustomerCard extends StatelessWidget {
  final Customer customer;
  final VoidCallback onTap;

  const CustomerCard({super.key, required this.customer, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: AppColors.surface2,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border, width: 1.0),
          boxShadow: [
            BoxShadow(color: Colors.black.withOpacity(0.5), blurRadius: 10, offset: const Offset(0, 4)),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 34, height: 34,
                  decoration: BoxDecoration(
                    color: AppColors.primaryDim,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Center(
                    child: Text(
                      customer.name.isNotEmpty ? customer.name[0].toUpperCase() : '?',
                      style: GoogleFonts.plusJakartaSans(
                          color: AppColors.primary, fontWeight: FontWeight.w800, fontSize: 16),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(customer.name, style: GoogleFonts.plusJakartaSans(
                          fontWeight: FontWeight.w700, fontSize: 14, color: AppColors.textPri, letterSpacing: -0.2)),
                      Text(customer.phoneNumber, style: GoogleFonts.plusJakartaSans(
                          fontSize: 11, color: AppColors.textSec)),
                    ],
                  ),
                ),
                CategoryBadge(category: customer.calculatedCategory),
              ],
            ),
            const SizedBox(height: 10),
            ChurnScoreBar(score: customer.churnScore),
            const SizedBox(height: 8),
            Row(
              children: [
                Text(customer.countryFlag, style: const TextStyle(fontSize: 13)),
                const SizedBox(width: 6),
                Flexible(
                  child: Text(
                    customer.countryPreferences.isNotEmpty
                        ? customer.countryPreferences.join(', ')
                        : (customer.preferredCountry ?? 'Not selected'),
                    style: GoogleFonts.plusJakartaSans(
                        fontSize: 11, color: AppColors.textSec, fontWeight: FontWeight.w600),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 8),
                const Spacer(),
                Text('${customer.daysInactive}d inactive',
                  style: GoogleFonts.plusJakartaSans(fontSize: 10, color: AppColors.textMuted, fontWeight: FontWeight.w600)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
