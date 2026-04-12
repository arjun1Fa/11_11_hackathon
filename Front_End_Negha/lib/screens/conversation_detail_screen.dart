import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../models/conversation.dart';
import '../services/supabase_service.dart';

class ConversationDetailScreen extends StatefulWidget {
  final String customerId;
  final String customerName;
  final String? preferredCountry;
  const ConversationDetailScreen({super.key, required this.customerId,
    required this.customerName, this.preferredCountry});
  @override
  State<ConversationDetailScreen> createState() => _ConversationDetailScreenState();
}

class _ConversationDetailScreenState extends State<ConversationDetailScreen> {
  List<Conversation> _messages = [];
  bool _isLoading = true;
  final ScrollController _scrollCtrl = ScrollController();
  dynamic _subscription;

  String get _flag {
    switch (widget.preferredCountry) {
      case 'Germany': return '🇩🇪'; case 'France': return '🇫🇷';
      case 'Netherlands': return '🇳🇱'; default: return '🌍';
    }
  }

  @override
  void initState() { super.initState(); _fetch(); _subscribe(); }
  @override
  void dispose() { _scrollCtrl.dispose(); _subscription?.unsubscribe(); super.dispose(); }

  Future<void> _fetch() async {
    final svc = context.read<SupabaseService>();
    try {
      final list = await svc.getConversationsForCustomer(widget.customerId);
      if (mounted) { setState(() { _messages = list; _isLoading = false; }); _scrollBottom(); }
    } catch (e) { if (mounted) setState(() => _isLoading = false); }
  }

  void _subscribe() {
    final svc = context.read<SupabaseService>();
    _subscription = svc.subscribeToConversations((r) {
      final c = Conversation.fromJson(r);
      if ((c.customerId == widget.customerId || c.phoneNumber == widget.customerId) && mounted) {
        setState(() => _messages.add(c)); _scrollBottom();
      }
    });
  }

  void _scrollBottom() => WidgetsBinding.instance.addPostFrameCallback((_) {
    if (_scrollCtrl.hasClients) _scrollCtrl.animateTo(
        _scrollCtrl.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
  });

  Future<void> _escalate() async {
    try {
      await context.read<SupabaseService>().createHandoff(
          widget.customerId, 'manual_escalation', widget.preferredCountry);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('⚠️ Escalated ${widget.customerName}'),
        backgroundColor: AppColors.sand));
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface2,
      appBar: AppBar(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
        title: Row(children: [
          Container(
            width: 32, height: 32,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Center(child: Text(
              widget.customerName.isNotEmpty ? widget.customerName[0].toUpperCase() : '?',
              style: GoogleFonts.plusJakartaSans(
                  color: Colors.white, fontWeight: FontWeight.w800, fontSize: 14),
            )),
          ),
          const SizedBox(width: 10),
          Expanded(child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('$_flag ${widget.customerName}',
                style: GoogleFonts.plusJakartaSans(
                    color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15),
                maxLines: 1, overflow: TextOverflow.ellipsis),
              Text('${_messages.length} messages',
                style: GoogleFonts.plusJakartaSans(
                    color: Colors.white.withOpacity(0.7), fontSize: 10)),
            ],
          )),
        ]),
        actions: [
          IconButton(
            icon: const Icon(Icons.warning_amber_rounded, size: 20),
            onPressed: _escalate,
            tooltip: 'Escalate',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.primary, strokeWidth: 2))
          : _messages.isEmpty
              ? Center(child: Text('No messages yet',
                  style: GoogleFonts.plusJakartaSans(color: AppColors.textMuted)))
              : ListView.builder(
                  controller: _scrollCtrl,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 16),
                  itemCount: _messages.length,
                  itemBuilder: (_, i) {
                    final msg = _messages[i];
                    final isInbound = msg.direction == 'inbound';
                    final showDate = i == 0 ||
                        !_sameDay(_messages[i - 1].timestamp, msg.timestamp);

                    return Column(children: [
                      if (showDate) _dateDivider(msg.timestamp),
                      _chatBubble(msg, isInbound),
                    ]);
                  },
                ),
    );
  }

  Widget _dateDivider(DateTime dt) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Center(child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(10),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 4)],
        ),
        child: Text(DateFormat('MMM dd, yyyy').format(dt),
          style: GoogleFonts.plusJakartaSans(fontSize: 10, color: AppColors.textMuted, fontWeight: FontWeight.w600)),
      )),
    );
  }

  Widget _chatBubble(Conversation msg, bool isInbound) {
    final time = DateFormat('HH:mm').format(msg.timestamp);
    return Align(
      alignment: isInbound ? Alignment.centerLeft : Alignment.centerRight,
      child: Container(
        margin: EdgeInsets.only(
          bottom: 6,
          left: isInbound ? 0 : 48,
          right: isInbound ? 48 : 0,
        ),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: isInbound ? Colors.white : AppColors.waBubbleOut,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isInbound ? 4 : 16),
            bottomRight: Radius.circular(isInbound ? 16 : 4),
          ),
          boxShadow: [BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 6, offset: const Offset(0, 2),
          )],
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          // Sender label
          if (!isInbound) Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Row(mainAxisSize: MainAxisSize.min, children: [
              const Icon(Icons.smart_toy_rounded, size: 11, color: AppColors.sage),
              const SizedBox(width: 4),
              Text('AI Bot', style: GoogleFonts.plusJakartaSans(
                  fontSize: 10, color: AppColors.sage, fontWeight: FontWeight.w700)),
            ]),
          ),
          // Message
          Text(msg.messageText, style: GoogleFonts.plusJakartaSans(
              fontSize: 13, color: AppColors.textPri, height: 1.4)),
          const SizedBox(height: 4),
          // Footer: time + intent/sentiment
          Row(mainAxisSize: MainAxisSize.min, children: [
            Text(time, style: GoogleFonts.plusJakartaSans(
                fontSize: 9, color: AppColors.textMuted)),
            if (!isInbound && msg.intentLabel != null) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(msg.intentLabel!,
                  style: GoogleFonts.plusJakartaSans(fontSize: 8, color: AppColors.primary, fontWeight: FontWeight.w600)),
              ),
            ],
            if (!isInbound && msg.sentiment != null) ...[
              const SizedBox(width: 4),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                decoration: BoxDecoration(
                  color: _sentimentColor(msg.sentiment!).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(msg.sentiment!,
                  style: GoogleFonts.plusJakartaSans(fontSize: 8, color: _sentimentColor(msg.sentiment!), fontWeight: FontWeight.w600)),
              ),
            ],
          ]),
        ]),
      ),
    );
  }

  Color _sentimentColor(String sentiment) {
    switch (sentiment.toLowerCase()) {
      case 'positive': return AppColors.sage;
      case 'negative': return AppColors.peach;
      default: return AppColors.textMuted;
    }
  }

  bool _sameDay(DateTime a, DateTime b) =>
      a.year == b.year && a.month == b.month && a.day == b.day;
}
