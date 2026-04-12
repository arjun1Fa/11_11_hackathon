import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../main.dart';

class CategoryBadge extends StatelessWidget {
  final String category;
  const CategoryBadge({super.key, required this.category});

  Color get _color {
    switch (category) {
      case 'Champion':       return AppColors.sage;
      case 'Loyal':          return AppColors.primary;
      case 'At Risk':        return AppColors.peach;
      case 'Potential':      return AppColors.sky;
      case 'Lost':           return AppColors.lavender;
      case 'Bargain Hunter': return AppColors.sand;
      case 'New':            return AppColors.sky;
      default:               return AppColors.textSec;
    }
  }

  Color get _bgColor {
    switch (category) {
      case 'Champion':       return AppColors.sageDim;
      case 'Loyal':          return AppColors.primaryDim;
      case 'At Risk':        return AppColors.peachDim;
      case 'Potential':      return AppColors.skyDim;
      case 'Lost':           return AppColors.lavenderDim;
      case 'Bargain Hunter': return AppColors.sandDim;
      case 'New':            return AppColors.skyDim;
      default:               return AppColors.surface2;
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
      child: Text(category,
        style: GoogleFonts.inter(fontSize: 10, color: _color, fontWeight: FontWeight.w600)),
    );
  }
}
