import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../models/package.dart';
import '../services/supabase_service.dart';
import '../widgets/country_package_card.dart';

class PackagesScreen extends StatefulWidget {
  const PackagesScreen({super.key});
  @override
  State<PackagesScreen> createState() => _PackagesScreenState();
}

class _PackagesScreenState extends State<PackagesScreen> {
  List<StudyAbroadPackage> _packages = [];
  bool _isLoading = true;

  @override
  void initState() { super.initState(); _fetch(); }

  Future<void> _fetch() async {
    final svc = context.read<SupabaseService>();
    try {
      final list = await svc.getAllPackages();
      if (mounted) setState(() { _packages = list; _isLoading = false; });
    } catch (e) { if (mounted) setState(() => _isLoading = false); }
  }

  @override
  Widget build(BuildContext context) {
    return _isLoading
        ? const Center(child: CircularProgressIndicator(color: AppColors.primary, strokeWidth: 2))
        : _packages.isEmpty
            ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                const Text('🌍', style: TextStyle(fontSize: 40)),
                const SizedBox(height: 12),
                Text('No packages found', style: GoogleFonts.plusJakartaSans(color: AppColors.textSec, fontSize: 14)),
              ]))
            : RefreshIndicator(onRefresh: _fetch, color: AppColors.primary,
                child: ListView.builder(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  itemCount: _packages.length,
                  itemBuilder: (_, i) => CountryPackageCard(package: _packages[i]),
                ));
  }
}
