import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../main.dart';

class ChurnScoreBar extends StatelessWidget {
  final double score;
  final bool showLabel;

  const ChurnScoreBar({super.key, required this.score, this.showLabel = true});

  Color get _color {
    if (score > 0.7) return AppColors.peach;
    if (score > 0.4) return AppColors.sand;
    return AppColors.sage;
  }

  String get _label {
    if (score > 0.7) return 'High';
    if (score > 0.4) return 'Medium';
    return 'Healthy';
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (showLabel)
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Risk level',
                style: GoogleFonts.inter(fontSize: 10, color: AppColors.textSec)),
              Text('${(score * 100).round()}% · $_label',
                style: GoogleFonts.inter(
                    fontSize: 10, color: _color, fontWeight: FontWeight.w600)),
            ],
          ),
        if (showLabel) const SizedBox(height: 4),
        ClipRRect(
          borderRadius: BorderRadius.circular(3),
          child: LinearProgressIndicator(
            value: score.clamp(0.0, 1.0),
            backgroundColor: AppColors.surface2,
            valueColor: AlwaysStoppedAnimation<Color>(_color),
            minHeight: 4,
          ),
        ),
      ],
    );
  }
}
