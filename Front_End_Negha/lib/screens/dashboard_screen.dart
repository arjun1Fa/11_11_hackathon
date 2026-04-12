import 'dart:async';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../services/supabase_service.dart';
import 'handoff_queue_screen.dart';
import 'appointment_queue_screen.dart';
import 'conversations_screen.dart';
import 'customers_screen.dart';
import 'voice_call_screen.dart';
import 'churn_list_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});
  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _selectedIndex = 0;
  bool _isLoading = true;
  Map<String, dynamic> _stats = {};
  List<Map<String, dynamic>> _hourlyData = [];
  Map<String, int> _categoryData = {};
  Timer? _refreshTimer;

  final List<_NavItem> _navItems = const [
    _NavItem(Icons.grid_view_rounded,     'Dashboard',     Color(0xFF0EA5E9)),
    _NavItem(Icons.warning_amber_rounded, 'Handoff Queue', Color(0xFFF43F5E)),
    _NavItem(Icons.calendar_month_rounded,'Appointments',  Color(0xFF8B5CF6)),
    _NavItem(Icons.chat_bubble_outline,   'Live Chat',     Color(0xFF10B981)),
    _NavItem(Icons.people_outline,        'All Students',  Color(0xFF38BDF8)),
    _NavItem(Icons.phone_callback_rounded,'Voice Calls',   Color(0xFFF59E0B)),
    _NavItem(Icons.crisis_alert_rounded,  'Churn Risk',    Color(0xFFF43F5E)),
  ];

  @override
  void initState() {
    super.initState();
    _fetchData();
    _refreshTimer = Timer.periodic(const Duration(seconds: 30), (_) => _fetchData());
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _fetchData() async {
    final svc = context.read<SupabaseService>();
    try {
      final r = await Future.wait([
        svc.getDashboardStats(),
        svc.getMessagesByHour(),
        svc.getCustomersByCategory(),
      ]);
      if (mounted) {
        setState(() {
          _stats = r[0] as Map<String, dynamic>;
          _hourlyData = r[1] as List<Map<String, dynamic>>;
          _categoryData = r[2] as Map<String, int>;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      drawer: _buildDrawer(),
      body: Column(
        children: [
          _topBar(),
          Expanded(
            child: IndexedStack(
              index: _selectedIndex,
              children: [
                _dashBody(),
                const HandoffQueueScreen(),
                const AppointmentQueueScreen(),
                const ConversationsScreen(),
                const CustomersScreen(),
                const VoiceCallScreen(),
                const ChurnListScreen(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDrawer() {
    return Drawer(
      backgroundColor: AppColors.sidebar,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.only(
          topRight: Radius.circular(24),
          bottomRight: Radius.circular(24),
        ),
      ),
      child: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 28),
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [AppColors.primary.withOpacity(0.15), Colors.transparent],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.primary.withOpacity(0.2)),
              ),
              child: Row(children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: AppColors.primary,
                    borderRadius: BorderRadius.circular(12),
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.primary.withOpacity(0.4),
                        blurRadius: 12,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: const Icon(Icons.blur_on_rounded, color: Colors.white, size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Smartilee',
                          style: GoogleFonts.plusJakartaSans(
                              color: Colors.white,
                              fontWeight: FontWeight.w800,
                              fontSize: 18,
                              letterSpacing: -0.5)),
                      Text('Admin Panel',
                          style: GoogleFonts.plusJakartaSans(
                              color: AppColors.sidebarText,
                              fontSize: 11,
                              fontWeight: FontWeight.w500)),
                    ],
                  ),
                ),
              ]),
            ),
            const SizedBox(height: 28),
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                itemCount: _navItems.length,
                itemBuilder: (_, i) {
                  final item = _navItems[i];
                  final selected = _selectedIndex == i;
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        borderRadius: BorderRadius.circular(12),
                        onTap: () {
                          setState(() => _selectedIndex = i);
                          Navigator.pop(context);
                        },
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                          decoration: BoxDecoration(
                            color: selected ? item.color.withOpacity(0.15) : Colors.transparent,
                            borderRadius: BorderRadius.circular(12),
                            border: selected ? Border.all(color: item.color.withOpacity(0.3)) : null,
                          ),
                          child: Row(children: [
                            Icon(item.icon,
                                size: 20,
                                color: selected ? item.color : AppColors.sidebarText),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Text(
                                item.label,
                                style: GoogleFonts.plusJakartaSans(
                                  fontSize: 13,
                                  fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                                  color: selected ? Colors.white : AppColors.sidebarText,
                                ),
                              ),
                            ),
                            if (i == 1 && (_stats['handoffCount'] ?? 0) > 0)
                              _badge('${_stats['handoffCount']}', AppColors.peach),
                            if (i == 2 && (_stats['appointmentCount'] ?? 0) > 0)
                              _badge('${_stats['appointmentCount']}', AppColors.lavender),
                            if (i == 6 && (_stats['highRisk'] ?? 0) > 0)
                              _badge('${_stats['highRisk']}', AppColors.peach),
                          ]),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
            Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.sidebarHover,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(children: [
                Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.person_outline, color: AppColors.primary, size: 16),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Admin',
                          style: GoogleFonts.plusJakartaSans(
                              color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
                      Text('Counsellor',
                          style: GoogleFonts.plusJakartaSans(
                              color: AppColors.sidebarText, fontSize: 10)),
                    ],
                  ),
                ),
              ]),
            ),
          ],
        ),
      ),
    );
  }

  Widget _badge(String text, Color color) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: color.withOpacity(0.2),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Text(text,
            style: GoogleFonts.plusJakartaSans(
                fontSize: 10, fontWeight: FontWeight.w800, color: color)),
      );

  Widget _topBar() {
    final isMobile = MediaQuery.of(context).size.width < 600;
    final item = _navItems[_selectedIndex];
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: AppColors.bg,
        border: const Border(bottom: BorderSide(color: AppColors.border, width: 1)),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withOpacity(0.03), blurRadius: 10, offset: const Offset(0, 2))
        ],
      ),
      padding: EdgeInsets.fromLTRB(8, isMobile ? 48 : 16, 16, 12),
      child: Row(
        children: [
          Builder(
            builder: (ctx) => IconButton(
              icon: const Icon(Icons.menu_rounded, color: AppColors.textPri, size: 24),
              onPressed: () => Scaffold.of(ctx).openDrawer(),
            ),
          ),
          const SizedBox(width: 4),
          Icon(item.icon, color: item.color, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Text(item.label,
                style: GoogleFonts.plusJakartaSans(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    color: AppColors.textPri,
                    letterSpacing: -0.5)),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: AppColors.sageDim,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppColors.sage.withOpacity(0.3)),
            ),
            child: Row(mainAxisSize: MainAxisSize.min, children: [
              Container(
                  width: 6,
                  height: 6,
                  decoration: const BoxDecoration(color: AppColors.sage, shape: BoxShape.circle)),
              const SizedBox(width: 6),
              Text('Live',
                  style: GoogleFonts.plusJakartaSans(
                      fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.sage)),
            ]),
          ),
        ],
      ),
    );
  }

  Widget _dashBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator(color: AppColors.primary, strokeWidth: 2));
    }
    final isMobile = MediaQuery.of(context).size.width < 600;

    return RefreshIndicator(
      onRefresh: _fetchData,
      color: AppColors.primary,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: EdgeInsets.all(isMobile ? 16 : 24),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _sectionLabel('LIVE METRICS'),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(
                child: _statCard('Total Students', '${_stats['totalActive'] ?? 0}',
                    Icons.school_rounded, AppColors.primary, AppColors.primaryDim)),
            const SizedBox(width: 10),
            Expanded(
                child: _statCard('Onboarding', '${_stats['onboarding'] ?? 0}',
                    Icons.person_add_alt_rounded, AppColors.lavender, AppColors.lavenderDim)),
          ]),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(
                child: GestureDetector(
              onTap: () => setState(() => _selectedIndex = 1),
              child: _statCard('Handoffs', '${_stats['handoffCount'] ?? 0}',
                  Icons.warning_amber_rounded, AppColors.peach, AppColors.peachDim),
            )),
            const SizedBox(width: 10),
            Expanded(
                child: GestureDetector(
              onTap: () => setState(() => _selectedIndex = 2),
              child: _statCard('Appointments', '${_stats['appointmentCount'] ?? 0}',
                  Icons.calendar_month_rounded, AppColors.sand, AppColors.sandDim),
            )),
          ]),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(
                child: GestureDetector(
              onTap: () => setState(() => _selectedIndex = 6),
              child: _statCard('High Risk', '${_stats['highRisk'] ?? 0}', Icons.crisis_alert_rounded,
                  AppColors.peach, AppColors.peachDim),
            )),
            const SizedBox(width: 10),
            Expanded(
                child: _statCard('AI Handled', '${_stats['aiReplyRate'] ?? 0}%',
                    Icons.smart_toy_rounded, AppColors.sage, AppColors.sageDim)),
          ]),
          SizedBox(height: isMobile ? 28 : 36),
          _sectionLabel('AI vs HUMAN DEFLECTION'),
          const SizedBox(height: 12),
          _card(Row(children: [
            _deflectionStat('AI Replies', '${_stats['aiReplies'] ?? 0}', AppColors.sage),
            const SizedBox(width: 16),
            _deflectionStat('Human', '${_stats['humanReplies'] ?? 0}', AppColors.sand),
            const SizedBox(width: 16),
            _deflectionStat('Messages', '${_stats['totalMessages'] ?? 0}', AppColors.primary),
          ])),
          SizedBox(height: isMobile ? 28 : 36),
          _sectionLabel('MESSAGE VOLUME BY HOUR'),
          const SizedBox(height: 12),
          _card(SizedBox(
            height: isMobile ? 140 : 180,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              physics: const BouncingScrollPhysics(),
              child: SizedBox(
                width: isMobile ? 600 : 800,
                child: BarChart(BarChartData(
                  borderData: FlBorderData(show: false),
                  gridData: const FlGridData(
                      show: true,
                      drawVerticalLine: false,
                      getDrawingHorizontalLine: _getHorizontalLine),
                  titlesData: FlTitlesData(
                    leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(
                        sideTitles: SideTitles(
                      showTitles: true,
                      interval: isMobile ? 8 : 4,
                      getTitlesWidget: (v, _) => Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Text('${v.toInt()}h',
                            style: GoogleFonts.outfit(
                                fontSize: 10,
                                color: AppColors.textSec,
                                fontWeight: FontWeight.w600)),
                      ),
                    )),
                  ),
                  barGroups: _hourlyData
                      .map((d) => BarChartGroupData(
                            x: d['hour'] as int,
                            barRods: [
                              BarChartRodData(
                                toY: (d['count'] as int).toDouble(),
                                color: AppColors.primary,
                                width: isMobile ? 8 : 10,
                                borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
                              )
                            ],
                          ))
                      .toList(),
                )),
              ),
            ),
          )),
          SizedBox(height: isMobile ? 28 : 36),
          _sectionLabel('STUDENT SEGMENTATION'),
          const SizedBox(height: 12),
          _categoryData.isNotEmpty
              ? _card(Padding(
                  padding: const EdgeInsets.all(32),
                  child: isMobile
                      ? Column(children: [
                          SizedBox(
                              width: 170,
                              height: 170,
                              child: PieChart(PieChartData(
                                sections: _buildPieSections(),
                                sectionsSpace: 6,
                                centerSpaceRadius: 55,
                              ))),
                          const SizedBox(height: 40),
                          _categoryLegend(),
                        ])
                      : Row(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            const SizedBox(width: 16),
                            SizedBox(
                                width: 170,
                                height: 170,
                                child: PieChart(PieChartData(
                                  sections: _buildPieSections(),
                                  sectionsSpace: 6,
                                  centerSpaceRadius: 55,
                                ))),
                            const SizedBox(width: 60),
                            Expanded(child: _categoryLegend()),
                          ],
                        ),
                ))
              : _card(Center(
                  child: Text('No data yet',
                      style: GoogleFonts.outfit(color: AppColors.textMuted, fontSize: 13)))),
          const SizedBox(height: 80),
        ]),
      ),
    );
  }

  static FlLine _getHorizontalLine(double value) => const FlLine(
        color: AppColors.border,
        strokeWidth: 1,
        dashArray: [5, 5],
      );

  List<PieChartSectionData> _buildPieSections() {
    return _categoryData.entries.toList().asMap().entries.map((e) {
      final color = _catColor(e.value.key);
      return PieChartSectionData(
        value: e.value.value.toDouble(),
        color: color,
        radius: 50,
        title: '',
      );
    }).toList();
  }

  Widget _categoryLegend() {
    final total = _categoryData.values.fold(0, (a, b) => a + b);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: _categoryData.entries.map((e) {
        final pct = total > 0 ? ((e.value / total) * 100).round() : 0;
        final color = _catColor(e.key);
        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Row(children: [
            Container(
                width: 10, height: 10, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
            const SizedBox(width: 10),
            Expanded(
                child: Text(e.key,
                    style: GoogleFonts.plusJakartaSans(
                        fontSize: 13, color: AppColors.textPri, fontWeight: FontWeight.w600))),
            Text('$pct%',
                style: GoogleFonts.plusJakartaSans(
                    fontSize: 13, color: color, fontWeight: FontWeight.w800)),
          ]),
        );
      }).toList(),
    );
  }

  Widget _sectionLabel(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 4),
        child: Text(text,
            style: GoogleFonts.plusJakartaSans(
                fontSize: 11,
                fontWeight: FontWeight.w800,
                color: AppColors.textMuted,
                letterSpacing: 1.5)),
      );

  Color _catColor(String cat) {
    switch (cat) {
      case 'Champion':
        return AppColors.sage;
      case 'Potential':
        return AppColors.sky;
      case 'At Risk':
        return AppColors.peach;
      default:
        return AppColors.textMuted;
    }
  }

  Widget _statCard(String label, String value, IconData icon, Color color, Color bgColor) =>
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withOpacity(0.2)),
          boxShadow: [
            BoxShadow(
                color: color.withOpacity(0.06), blurRadius: 16, offset: const Offset(0, 4))
          ],
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(color: bgColor, borderRadius: BorderRadius.circular(10)),
              child: Icon(icon, color: color, size: 18)),
          const SizedBox(height: 12),
          Text(value,
              style: GoogleFonts.plusJakartaSans(
                  fontSize: 24,
                  fontWeight: FontWeight.w800,
                  color: AppColors.textPri,
                  letterSpacing: -0.5)),
          const SizedBox(height: 2),
          Text(label,
              style: GoogleFonts.plusJakartaSans(
                  fontSize: 11, color: AppColors.textSec, fontWeight: FontWeight.w500),
              maxLines: 1,
              overflow: TextOverflow.ellipsis),
        ]),
      );

  Widget _deflectionStat(String label, String value, Color color) => Expanded(
        child: Column(children: [
          Text(value,
              style: GoogleFonts.plusJakartaSans(
                  fontSize: 22, fontWeight: FontWeight.w800, color: color)),
          const SizedBox(height: 4),
          Text(label, style: GoogleFonts.plusJakartaSans(fontSize: 11, color: AppColors.textSec)),
        ]),
      );

  Widget _card(Widget child) => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border),
          boxShadow: [
            BoxShadow(
                color: Colors.black.withOpacity(0.03), blurRadius: 12, offset: const Offset(0, 4))
          ],
        ),
        child: child,
      );
}

class _NavItem {
  final IconData icon;
  final String label;
  final Color color;
  const _NavItem(this.icon, this.label, this.color);
}
