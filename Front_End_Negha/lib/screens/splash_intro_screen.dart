import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../models/conversation.dart';
import '../models/package.dart';
import '../services/supabase_service.dart';
import 'dashboard_screen.dart';

class SplashIntroScreen extends StatefulWidget {
  const SplashIntroScreen({super.key});
  @override
  State<SplashIntroScreen> createState() => _SplashIntroScreenState();
}

class _SplashIntroScreenState extends State<SplashIntroScreen>
    with TickerProviderStateMixin {
  final PageController _pageCtrl = PageController();
  int _currentPage = 0;

  late AnimationController _rippleCtrl;
  late AnimationController _fadeCtrl;
  late AnimationController _exitCtrl; // NEW: for falling exit
  late Animation<double> _logoFade;
  late Animation<double> _textFade;
  late Animation<Offset> _fallingOffset; 
  late Animation<double> _fallingFade;

  // Page 2: chat & packages
  List<Conversation> _conversations = [];
  List<StudyAbroadPackage> _packages = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _rippleCtrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 3000))..repeat();
    _fadeCtrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 2000))..forward();
    
    _exitCtrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 800));

    _logoFade = CurvedAnimation(parent: _fadeCtrl,
        curve: const Interval(0.0, 0.5, curve: Curves.easeOut));
    _textFade = CurvedAnimation(parent: _fadeCtrl,
        curve: const Interval(0.35, 1.0, curve: Curves.easeOut));

    _fallingOffset = Tween<Offset>(
      begin: Offset.zero,
      end: const Offset(0, 1.5), // Falling down
    ).animate(CurvedAnimation(parent: _exitCtrl, curve: Curves.easeInBack));

    _fallingFade = Tween<double>(begin: 1.0, end: 0.0).animate(
      CurvedAnimation(parent: _exitCtrl, curve: const Interval(0.0, 0.5)));

    _loadData();
    
    // Automatically move to dashboard after animation
    Future.delayed(const Duration(milliseconds: 2500), () {
      if (mounted) _enterDashboard();
    });
  }

  Future<void> _loadData() async {
    try {
      final svc = context.read<SupabaseService>();
      final results = await Future.wait([
        svc.getConversations(),
        svc.getAllPackages(),
      ]);
      if (mounted) setState(() {
        _conversations = results[0] as List<Conversation>;
        _packages = results[1] as List<StudyAbroadPackage>;
        _isLoading = false;
      });
    } catch (_) { if (mounted) setState(() => _isLoading = false); }
  }

  @override
  void dispose() { 
    _rippleCtrl.dispose(); 
    _fadeCtrl.dispose(); 
    _exitCtrl.dispose(); 
    _pageCtrl.dispose(); 
    super.dispose(); 
  }

  void _next() async {
    if (_currentPage == 0) {
      // Perform raindrop falling exit for first page
      await _exitCtrl.forward();
      _pageCtrl.jumpToPage(1);
      _exitCtrl.reset();
    } else {
      _pageCtrl.nextPage(duration: const Duration(milliseconds: 500), curve: Curves.easeInOutCubic);
    }
  }
  void _back() => _pageCtrl.previousPage(duration: const Duration(milliseconds: 500), curve: Curves.easeInOutCubic);

  void _enterDashboard() => Navigator.of(context).pushReplacement(
    PageRouteBuilder(
      pageBuilder: (_, __, ___) => const DashboardScreen(),
      transitionsBuilder: (_, a, __, c) => FadeTransition(opacity: a, child: c),
      transitionDuration: const Duration(milliseconds: 500),
    ),
  );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: Stack(
        children: [
          PageView(
            controller: _pageCtrl,
            onPageChanged: (p) => setState(() => _currentPage = p),
            children: [_page1Splash(), _page2Chat(), _page3Dashboard()],
          ),
          // Dots
          Positioned(
            bottom: 28, left: 0, right: 0,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(3, (i) {
                final active = _currentPage == i;
                return AnimatedContainer(
                  duration: const Duration(milliseconds: 250),
                  margin: const EdgeInsets.symmetric(horizontal: 3),
                  width: active ? 18 : 5, height: 5,
                  decoration: BoxDecoration(
                    color: active ? AppColors.primary : AppColors.border,
                    borderRadius: BorderRadius.circular(3)),
                );
              }),
            ),
          ),
        ],
      ),
    );
  }

  // ═══════════════════════════════════════════════════════════
  // PAGE 1 — Raindrop Splash
  // ═══════════════════════════════════════════════════════════
  Widget _page1Splash() {
    final isMobile = MediaQuery.of(context).size.width < 600;
    return Stack(
      children: [
        // Sleek glowing orb effect for dark mode
        Positioned.fill(child: DecoratedBox(decoration: BoxDecoration(
          gradient: RadialGradient(
            center: const Alignment(0, -0.15), radius: 0.8,
            colors: [AppColors.primaryDim, AppColors.bg],
          ),
        ))),

        // Ripples
        Center(
          child: AnimatedBuilder(
            animation: _rippleCtrl,
            builder: (_, __) => CustomPaint(
              painter: _DropRipplePainter(_rippleCtrl.value),
              child: const SizedBox(width: 280, height: 280),
            ),
          ),
        ),

        // Content
        Center(
          child: AnimatedBuilder(
            animation: _exitCtrl,
            builder: (context, child) => SlideTransition(
              position: _fallingOffset,
              child: FadeTransition(
                opacity: _fallingFade,
                child: child,
              ),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Logo Glow Box
                FadeTransition(opacity: _logoFade, child: Container(
                  width: isMobile ? 54 : 64, height: isMobile ? 54 : 64,
                  decoration: BoxDecoration(
                    color: AppColors.surface, borderRadius: BorderRadius.circular(isMobile ? 15 : 18),
                    border: Border.all(color: AppColors.primary.withOpacity(0.5)),
                    boxShadow: [
                      BoxShadow(color: AppColors.primary.withOpacity(0.3), blurRadius: 20, offset: const Offset(0, 0)),
                      BoxShadow(color: AppColors.primaryDim, blurRadius: 40, spreadRadius: -5),
                    ],
                  ),
                  child: Icon(Icons.blur_on_rounded, color: AppColors.primary, size: isMobile ? 30 : 36),
                )),
                const SizedBox(height: 22),

                // Name
                FadeTransition(opacity: _logoFade, child: TextTheme.of(context).displayLarge?.copyWith(
                  fontSize: isMobile ? 36 : 44,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -1.5,
                ) != null ? Text('Smartilee',
                  style: Theme.of(context).textTheme.displayLarge?.copyWith(fontSize: isMobile ? 36 : 44, letterSpacing: -1.5)) : Text('Smartilee',
                  style: GoogleFonts.plusJakartaSans(fontSize: isMobile ? 36 : 44, fontWeight: FontWeight.w800,
                      color: AppColors.textPri, letterSpacing: -1.5))),
                const SizedBox(height: 12),

                // Tagline
                FadeTransition(opacity: _textFade, child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  child: Text(
                    'AI Study Abroad Assistant on WhatsApp',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: AppColors.textSec, fontSize: isMobile ? 14 : 16)),
                )),
                const SizedBox(height: 24),

                // Country pills
                FadeTransition(opacity: _textFade, child: Wrap(
                  spacing: 8, runSpacing: 8, alignment: WrapAlignment.center,
                  children: [_pill('🇩🇪'), _pill('🇫🇷'), _pill('🇳🇱')],
                )),
                const SizedBox(height: 44),

                // CTA
                FadeTransition(opacity: _textFade, child: GestureDetector(
                  onTap: _next,
                  child: Container(
                    padding: EdgeInsets.symmetric(horizontal: isMobile ? 32 : 26, vertical: 14),
                    decoration: BoxDecoration(
                      color: AppColors.surface2, borderRadius: BorderRadius.circular(32),
                      border: Border.all(color: AppColors.primary.withOpacity(0.6), width: 1.5),
                      boxShadow: [BoxShadow(color: AppColors.primary.withOpacity(0.3), blurRadius: 25, offset: const Offset(0, 0))],
                    ),
                    child: Row(mainAxisSize: MainAxisSize.min, children: [
                      Text('View Live Chat', style: GoogleFonts.plusJakartaSans(
                          color: AppColors.primary, fontWeight: FontWeight.w800, fontSize: 15, letterSpacing: 0.2)),
                      const SizedBox(width: 8),
                      const Icon(Icons.arrow_forward_rounded, color: AppColors.primary, size: 16),
                    ]),
                  ),
                )),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _pill(String flag) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
    decoration: BoxDecoration(
      color: AppColors.surface, borderRadius: BorderRadius.circular(20),
      border: Border.all(color: AppColors.border)),
    child: Text(flag, style: const TextStyle(fontSize: 18)),
  );

  // ═══════════════════════════════════════════════════════════
  // PAGE 2 — WhatsApp-style Chat
  // ═══════════════════════════════════════════════════════════
  Widget _page2Chat() {
    final isMobile = MediaQuery.of(context).size.width < 600;
    return Column(
      children: [
        // WA-style header
        Container(
          padding: EdgeInsets.fromLTRB(16, isMobile ? 44 : 48, 16, 12),
          decoration: const BoxDecoration(
            color: AppColors.primary,
          ),
          child: Row(
            children: [
              GestureDetector(
                onTap: _back,
                child: const Icon(Icons.arrow_back, color: Colors.white, size: 20)),
              const SizedBox(width: 8),
              Container(
                width: isMobile ? 32 : 36, height: isMobile ? 32 : 36,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  shape: BoxShape.circle),
                child: Icon(Icons.smart_toy_rounded, color: Colors.white, size: isMobile ? 16 : 18),
              ),
              const SizedBox(width: 10),
              Expanded(child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Smartilee AI Bot', style: GoogleFonts.plusJakartaSans(
                      color: Colors.white, fontWeight: FontWeight.w800, fontSize: isMobile ? 15 : 16, letterSpacing: -0.2)),
                  Text(_conversations.isNotEmpty
                      ? '${_conversations.length} messages'
                      : 'Waiting for messages...',
                    style: GoogleFonts.plusJakartaSans(color: Colors.white.withOpacity(0.8), fontSize: 10, fontWeight: FontWeight.w600)),
                ],
              )),
              Icon(Icons.more_vert, color: Colors.white, size: isMobile ? 18 : 20),
            ],
          ),
        ),

        // Chat body
        Expanded(
          child: Container(
            decoration: const BoxDecoration(
              color: AppColors.bg, // Clean background for tiles
            ),
            child: _isLoading
                ? Center(child: CircularProgressIndicator(
                    color: AppColors.primary, strokeWidth: 2))
                : _conversations.isEmpty
                    ? Center(child: Text('Waiting for messages...', style: GoogleFonts.outfit(color: AppColors.textMuted)))
                    : ListView(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                        children: [
                          // 1. Student Queries Dropdown
                          Theme(
                            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
                            child: ExpansionTile(
                              initiallyExpanded: true,
                              leading: const Icon(Icons.person_pin_circle_outlined, color: AppColors.primary),
                              title: Text('Student Queries', 
                                style: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w800, color: AppColors.textPri, fontSize: 15)),
                              subtitle: Text('${_conversations.where((c) => c.direction == 'inbound').length} inbound messages',
                                style: GoogleFonts.plusJakartaSans(fontSize: 11, color: AppColors.textSec, fontWeight: FontWeight.w500)),
                              children: _conversations
                                  .where((c) => c.direction == 'inbound')
                                  .map((c) => _messageTile(c))
                                  .toList(),
                            ),
                          ),
                          const SizedBox(height: 12),
                          // 2. Business Responses Dropdown
                          Theme(
                            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
                            child: ExpansionTile(
                              initiallyExpanded: true,
                              leading: const Icon(Icons.smart_toy_outlined, color: AppColors.sage),
                              title: Text('Business Responses', 
                                style: GoogleFonts.outfit(fontWeight: FontWeight.w800, color: AppColors.textPri)),
                              subtitle: Text('${_conversations.where((c) => c.direction == 'outbound').length} automated/human replies',
                                style: GoogleFonts.outfit(fontSize: 11, color: AppColors.textSec)),
                              children: _conversations
                                  .where((c) => c.direction == 'outbound')
                                  .map((c) => _messageTile(c))
                                  .toList(),
                            ),
                          ),
                        ],
                      ),
          ),
        ),

        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
          color: AppColors.surface2,
          child: Row(children: [
            const Icon(Icons.emoji_emotions_outlined, color: AppColors.textMuted, size: 22),
            const SizedBox(width: 8),
            Expanded(child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: AppColors.surface, borderRadius: BorderRadius.circular(24),
                border: Border.all(color: AppColors.border)),
              child: Text('Type a message', style: GoogleFonts.outfit(
                  color: AppColors.textMuted, fontSize: 13)),
            )),
            const SizedBox(width: 8),
            GestureDetector(
              onTap: _next,
              child: Container(
                width: 44, height: 44,
                decoration: BoxDecoration(color: AppColors.primary, shape: BoxShape.circle,
                  boxShadow: [BoxShadow(color: AppColors.primary.withOpacity(0.2), blurRadius: 8, offset: const Offset(0, 3))],
                ),
                child: const Icon(Icons.arrow_forward_rounded, color: Colors.white, size: 20),
              ),
            ),
          ]),
        ),
        if (isMobile) const SizedBox(height: 20),
      ],
    );
  }

  Widget _messageTile(Conversation msg) {
    final time = '${msg.timestamp.hour.toString().padLeft(2, '0')}:${msg.timestamp.minute.toString().padLeft(2, '0')}';
    return Container(
      margin: const EdgeInsets.only(bottom: 2, left: 16),
      decoration: const BoxDecoration(border: Border(left: BorderSide(color: AppColors.border, width: 2))),
      child: ListTile(
        dense: true,
        title: Text(msg.messageText, 
          style: GoogleFonts.outfit(fontSize: 13, height: 1.4, color: AppColors.textPri)),
        subtitle: Row(
          children: [
            Text(time, style: GoogleFonts.outfit(fontSize: 10, color: AppColors.textMuted)),
            if (msg.direction == 'outbound') ...[
              const SizedBox(width: 8),
              const Icon(Icons.auto_awesome, size: 10, color: AppColors.sage),
              const SizedBox(width: 4),
              Text('AI Response', style: GoogleFonts.outfit(fontSize: 10, color: AppColors.sage)),
            ],
          ],
        ),
      ),
    );
  }

  // ═══════════════════════════════════════════════════════════
  // PAGE 3 — Dashboard Preview + Enter
  // ═══════════════════════════════════════════════════════════
  Widget _page3Dashboard() {
    final isMobile = MediaQuery.of(context).size.width < 600;
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 32, 24, 70),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('DASHBOARD', style: GoogleFonts.plusJakartaSans(fontSize: 12,
                color: AppColors.textMuted, fontWeight: FontWeight.w800, letterSpacing: 2.0)),
            const SizedBox(height: 12),
            Text('Analytics & Results', style: Theme.of(context).textTheme.displayMedium),
            const SizedBox(height: 8),
            Text('Real-time stats, student management, and retention.',
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: AppColors.textSec, height: 1.6)),
            const SizedBox(height: 32),

            // Preview cards
            Expanded(child: ListView(children: [
              _previewCard(Icons.grid_view_rounded, 'Live Stats',
                  'Message volume, AI reply rate, conversions, and risk', AppColors.sky, AppColors.skyDim),
              _previewCard(Icons.people_outline_rounded, 'Student Profiles',
                  'Student country, education, IELTS, and risk status', AppColors.sage, AppColors.sageDim),
              _previewCard(Icons.flight_takeoff_outlined, 'Packages',
                  'Germany, France, Netherlands — tuition, unis, scholarships', AppColors.lavender, AppColors.lavenderDim),
              _previewCard(Icons.headset_mic_outlined, 'Handoff Queue',
                  'Human escalations resolved from the dashboard', AppColors.sand, AppColors.sandDim),
              _previewCard(Icons.bar_chart_rounded, 'Charts',
                  'Hourly message volume, student category breakdown', AppColors.primary, AppColors.primaryDim),
              _previewCard(Icons.warning_amber_outlined, 'At the verge of leaving',
                  'Risk students with one-tap re-engagement', AppColors.peach, AppColors.peachDim),
            ])),

            const SizedBox(height: 16),
            Row(children: [
              TextButton(onPressed: _back, child: Text(isMobile ? 'Back' : '<- Chat',
                style: GoogleFonts.outfit(color: AppColors.textMuted, fontSize: 13, fontWeight: FontWeight.w600))),
              const Spacer(),
              GestureDetector(
                onTap: _enterDashboard,
                child: Container(
                  padding: EdgeInsets.symmetric(horizontal: isMobile ? 24 : 32, vertical: 16),
                  decoration: BoxDecoration(
                    color: AppColors.surface2, borderRadius: BorderRadius.circular(32),
                    border: Border.all(color: AppColors.primary.withOpacity(0.6), width: 1.5),
                    boxShadow: [BoxShadow(color: AppColors.primary.withOpacity(0.3), blurRadius: 25, offset: const Offset(0, 0))],
                  ),
                  child: Row(mainAxisSize: MainAxisSize.min, children: [
                    Text('Launch Dashboard', style: GoogleFonts.plusJakartaSans(
                        color: AppColors.primary, fontWeight: FontWeight.w800, fontSize: isMobile ? 14 : 16)),
                    const SizedBox(width: 10),
                    const Icon(Icons.rocket_launch_rounded, color: AppColors.primary, size: 18),
                  ]),
                ),
              ),
            ]),
          ],
        ),
      ),
    );
  }

  Widget _previewCard(IconData icon, String title, String desc, Color color, Color bgColor) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface, borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border)),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          width: 36, height: 36,
          decoration: BoxDecoration(color: bgColor, borderRadius: BorderRadius.circular(9)),
          child: Icon(icon, size: 18, color: color),
        ),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: GoogleFonts.outfit(fontSize: 14, fontWeight: FontWeight.w800, color: AppColors.textPri)),
          const SizedBox(height: 2),
          Text(desc, style: GoogleFonts.outfit(fontSize: 11, color: AppColors.textSec, height: 1.4)),
        ])),
      ]),
    );
  }
}

// ── Raindrop ripple painter ──────────────────────────────────────────────────
class _DropRipplePainter extends CustomPainter {
  final double progress;
  _DropRipplePainter(this.progress);

  @override
  void paint(Canvas canvas, Size size) {
    final c = Offset(size.width / 2, size.height / 2);
    final maxR = size.width / 2 * 0.85;

    for (int i = 0; i < 4; i++) {
      final t = ((progress + i * 0.25) % 1.0);
      final radius = t * maxR;
      final opacity = (1.0 - t) * 0.5;
      canvas.drawCircle(c, radius, Paint()
        ..color = AppColors.primary.withOpacity(opacity)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.0);
    }

    // Small glowing dot at center
    canvas.drawCircle(c, 3, Paint()..color = AppColors.primary.withOpacity(1.0));
    canvas.drawCircle(c, 8, Paint()..color = AppColors.primary.withOpacity(0.2));
  }

  @override
  bool shouldRepaint(_DropRipplePainter o) => o.progress != progress;
}
