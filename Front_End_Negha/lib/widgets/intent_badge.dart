import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../main.dart';

class IntentBadge extends StatelessWidget {
  final String intent;
  const IntentBadge({super.key, required this.intent});

  Color get _color {
    switch (intent) {
      case 'package_enquiry':   return AppColors.sage;
      case 'visa_question':     return AppColors.sky;
      case 'scholarship_query': return AppColors.lavender;
      case 'complaint':         return AppColors.peach;
      case 'churn_risk':        return AppColors.sand;
      default:                  return AppColors.textSec;
    }
  }

  Color get _bgColor {
    switch (intent) {
      case 'package_enquiry':   return AppColors.sageDim;
      case 'visa_question':     return AppColors.skyDim;
      case 'scholarship_query': return AppColors.lavenderDim;
      case 'complaint':         return AppColors.peachDim;
      case 'churn_risk':        return AppColors.sandDim;
      default:                  return AppColors.surface2;
    }
  }

  String get _label {
    switch (intent) {
      case 'package_enquiry':   return 'Package';
      case 'visa_question':     return 'Visa';
      case 'scholarship_query': return 'Scholarship';
      case 'complaint':         return 'Complaint';
      case 'churn_risk':        return 'Churn';
      default:                  return 'General';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(
        color: _bgColor,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(_label,
        style: GoogleFonts.inter(fontSize: 10, color: _color, fontWeight: FontWeight.w600)),
    );
  }
}
