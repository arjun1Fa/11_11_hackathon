import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/dashboard_screen.dart';
import 'services/supabase_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await Supabase.initialize(
    url: const String.fromEnvironment(
      'SUPABASE_URL',
      defaultValue: 'https://yoirzyoeshlyqxilpygm.supabase.co',
    ),
    anonKey: const String.fromEnvironment(
      'SUPABASE_ANON_KEY',
      defaultValue: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvaXJ6eW9lc2hseXF4aWxweWdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU5MDg0ODksImV4cCI6MjA5MTQ4NDQ4OX0.YVsvtMx4dAIl3PhHLa6MOI1qMmhpXq-XeMuwKLMJOQM',
    ),
  );

  runApp(
    Provider<SupabaseService>(
      create: (_) => SupabaseService(),
      child: const SmartileeApp(),
    ),
  );
}

// ─── Premium White & Sky Blue Palette ────────────────────────────────────────
class AppColors {
  // Backgrounds
  static const bg       = Color(0xFFFFFFFF);
  static const surface  = Color(0xFFF8FAFC);
  static const surface2 = Color(0xFFF1F5F9);
  static const border   = Color(0xFFE2E8F0);

  // Sidebar — dark slate
  static const sidebar     = Color(0xFF0F172A);
  static const sidebarHover= Color(0xFF1E293B);
  static const sidebarText = Color(0xFF94A3B8);

  // Primary accent — Sky Blue
  static const primary    = Color(0xFF0EA5E9);
  static const primaryDim = Color(0xFFE0F2FE);

  // Semantic hues
  static const sage      = Color(0xFF10B981);
  static const sageDim   = Color(0xFFD1FAE5);
  static const peach     = Color(0xFFF43F5E);
  static const peachDim  = Color(0xFFFFE4E6);
  static const sand      = Color(0xFFF59E0B);
  static const sandDim   = Color(0xFFFEF3C7);
  static const lavender  = Color(0xFF8B5CF6);
  static const lavenderDim = Color(0xFFEDE9FE);
  static const sky       = Color(0xFF38BDF8);
  static const skyDim    = Color(0xFFE0F2FE);

  // WhatsApp greens
  static const waGreen     = Color(0xFF25D366);
  static const waBubbleOut = Color(0xFFDCF8C6);
  static const waBubbleIn  = Color(0xFFFFFFFF);
  static const waBg        = Color(0xFFECE5DD);

  // Text
  static const textPri   = Color(0xFF0F172A);
  static const textSec   = Color(0xFF475569);
  static const textMuted = Color(0xFF94A3B8);

  // Aliases
  static const green = sage; static const emerald = sage;
  static const amber = sand; static const red = peach;
  static const rose = peach; static const cyan = sky;
  static const teal = sky;  static const violet = lavender;
  static const slate = lavender;
}

class SmartileeApp extends StatelessWidget {
  const SmartileeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smartilee — Study Abroad Dashboard',
      debugShowCheckedModeBanner: false,
      theme: _buildTheme(),
      home: const DashboardScreen(),
    );
  }

  ThemeData _buildTheme() {
    final base = ThemeData(brightness: Brightness.light);
    return base.copyWith(
      colorScheme: ColorScheme.light(
        primary: AppColors.primary,
        secondary: AppColors.primary,
        surface: AppColors.surface,
        error: AppColors.red,
      ),
      scaffoldBackgroundColor: AppColors.bg,
      textTheme: GoogleFonts.plusJakartaSansTextTheme(base.textTheme).copyWith(
        displayLarge: GoogleFonts.plusJakartaSans(
          fontSize: 32, fontWeight: FontWeight.w800,
          color: AppColors.primary, letterSpacing: -1.0, height: 1.1,
        ),
        displayMedium: GoogleFonts.plusJakartaSans(
          fontSize: 24, fontWeight: FontWeight.w800,
          color: AppColors.primary, letterSpacing: -0.5, height: 1.2,
        ),
        titleLarge: GoogleFonts.plusJakartaSans(
          fontSize: 20, fontWeight: FontWeight.w700,
          color: AppColors.primary, letterSpacing: -0.2,
        ),
        bodyLarge: GoogleFonts.plusJakartaSans(
          fontSize: 16, color: AppColors.textPri, height: 1.5,
        ),
        bodyMedium: GoogleFonts.plusJakartaSans(
          fontSize: 14, color: AppColors.textSec, height: 1.5,
        ),
        labelSmall: GoogleFonts.plusJakartaSans(
          fontSize: 11, fontWeight: FontWeight.w800,
          letterSpacing: 1.2, color: AppColors.textMuted,
        ),
      ).apply(bodyColor: AppColors.textPri, displayColor: AppColors.textPri),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          foregroundColor: Colors.white,
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w700, fontSize: 14),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
        ),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.bg,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: GoogleFonts.plusJakartaSans(
          fontSize: 18, fontWeight: FontWeight.w800, color: AppColors.textPri,
        ),
        iconTheme: const IconThemeData(color: AppColors.textPri),
      ),
    );
  }
}
