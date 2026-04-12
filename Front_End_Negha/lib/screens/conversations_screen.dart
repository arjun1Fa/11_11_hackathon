import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../models/conversation.dart';
import '../services/supabase_service.dart';
import 'conversation_detail_screen.dart';

class ConversationsScreen extends StatefulWidget {
  const ConversationsScreen({super.key});
  @override
  State<ConversationsScreen> createState() => _ConversationsScreenState();
}

class _ConversationsScreenState extends State<ConversationsScreen> {
  List<Conversation> _allConversations = [];
  List<_ChatThread> _threads = [];
  List<_ChatThread> _filteredThreads = [];
  bool _isLoading = true;
  String _search = '';
  dynamic _subscription;

  @override
  void initState() {
    super.initState();
    _fetch();
    _subscribe();
  }

  @override
  void dispose() {
    _subscription?.unsubscribe();
    super.dispose();
  }

  Future<void> _fetch() async {
    final svc = context.read<SupabaseService>();
    try {
      final list = await svc.getConversations();
      if (mounted) {
        setState(() {
          _allConversations = list;
          _buildThreads();
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _subscribe() {
    final svc = context.read<SupabaseService>();
    _subscription = svc.subscribeToConversations((newRow) async {
      final conv = Conversation.fromJson(newRow);
      if (mounted) {
        setState(() {
          _allConversations.insert(0, conv);
          _buildThreads();
        });
      }
    });
  }

  void _buildThreads() {
    final Map<String, _ChatThread> threadMap = {};
    for (final conv in _allConversations) {
      final key = conv.customerId ?? conv.phoneNumber ?? conv.id;
      if (!threadMap.containsKey(key)) {
        threadMap[key] = _ChatThread(
          customerId: conv.customerId,
          phoneNumber: conv.phoneNumber,
          customerName: conv.customerName,
          preferredCountry: conv.preferredCountry,
          lastMessage: conv,
          messageCount: 0,
          inboundCount: 0,
        );
      }
      threadMap[key]!.messageCount++;
      if (conv.direction == 'inbound') threadMap[key]!.inboundCount++;
      if (conv.timestamp.isAfter(threadMap[key]!.lastMessage.timestamp)) {
        threadMap[key]!.lastMessage = conv;
        threadMap[key]!.customerName ??= conv.customerName;
        threadMap[key]!.preferredCountry ??= conv.preferredCountry;
      }
    }
    _threads = threadMap.values.toList()
      ..sort((a, b) => b.lastMessage.timestamp.compareTo(a.lastMessage.timestamp));
    _applySearch();
  }

  void _applySearch() {
    if (_search.isEmpty) {
      _filteredThreads = _threads;
    } else {
      final q = _search.toLowerCase();
      _filteredThreads = _threads.where((t) {
        return (t.customerName?.toLowerCase().contains(q) ?? false) ||
            (t.phoneNumber?.contains(q) ?? false);
      }).toList();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      // Premium Search Header
      _buildHeader(),

      // Conversation List
      Expanded(
        child: _isLoading
            ? const Center(
                child: CircularProgressIndicator(color: AppColors.primary, strokeWidth: 2))
            : _filteredThreads.isEmpty
                ? _buildEmptyState()
                : RefreshIndicator(
                    onRefresh: _fetch,
                    color: AppColors.primary,
                    child: ListView.builder(
                      padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                      itemCount: _filteredThreads.length,
                      itemBuilder: (_, i) {
                        return _buildThreadCard(_filteredThreads[i]);
                      },
                    ),
                  ),
      ),
    ]);
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
      decoration: BoxDecoration(
        color: AppColors.bg,
        border: Border(bottom: BorderSide(color: AppColors.border, width: 0.5)),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        TextField(
          decoration: InputDecoration(
            hintText: 'Search conversations...',
            hintStyle: GoogleFonts.plusJakartaSans(color: AppColors.textMuted, fontSize: 13),
            prefixIcon: const Icon(Icons.forum_rounded, color: AppColors.primary, size: 20),
            filled: true,
            fillColor: AppColors.surface2,
            border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
            contentPadding: const EdgeInsets.symmetric(vertical: 0),
          ),
          style: GoogleFonts.plusJakartaSans(
              color: AppColors.textPri, fontSize: 13, fontWeight: FontWeight.w600),
          onChanged: (v) {
            setState(() {
              _search = v;
              _applySearch();
            });
          },
        ),
      ]),
    );
  }

  Widget _buildThreadCard(_ChatThread thread) {
    final msg = thread.lastMessage;
    final isAI = msg.direction == 'outbound' && msg.actionTaken != 'human_active';
    final isNew = DateTime.now().difference(msg.timestamp).inMinutes < 10;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
            color: isNew ? AppColors.primary.withOpacity(0.3) : AppColors.border,
            width: isNew ? 1.5 : 1.0),
        boxShadow: [
          BoxShadow(
              color: isNew ? AppColors.primary.withOpacity(0.08) : Colors.black.withOpacity(0.02),
              blurRadius: 12,
              offset: const Offset(0, 4)),
        ],
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => _navigateToDetail(thread),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(children: [
            _avatar(thread),
            const SizedBox(width: 14),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                   Expanded(child: Text(thread.customerName ?? thread.phoneNumber ?? 'Unknown',
                      style: GoogleFonts.plusJakartaSans(
                          fontSize: 14, fontWeight: FontWeight.w800, color: AppColors.textPri))),
                   Text(_formatTime(msg.timestamp),
                      style: GoogleFonts.plusJakartaSans(fontSize: 10, color: AppColors.textMuted)),
                ]),
                const SizedBox(height: 4),
                Row(children: [
                   if (isAI) _aiBadge(),
                   Expanded(child: Text(msg.messageText,
                      style: GoogleFonts.plusJakartaSans(fontSize: 12, color: AppColors.textSec),
                      maxLines: 1, overflow: TextOverflow.ellipsis)),
                ]),
              ]),
            ),
            const SizedBox(width: 8),
            _unreadCount(thread.messageCount),
          ]),
        ),
      ),
    );
  }

  Widget _avatar(_ChatThread thread) => Container(
    width: 48, height: 48,
    decoration: BoxDecoration(
      color: thread.lastMessage.direction == 'inbound' ? AppColors.primaryDim : AppColors.sageDim,
      borderRadius: BorderRadius.circular(14),
    ),
    child: Center(child: Text(
      (thread.customerName ?? thread.phoneNumber ?? '?')[0].toUpperCase(),
      style: GoogleFonts.plusJakartaSans(
          fontSize: 18, fontWeight: FontWeight.w800,
          color: thread.lastMessage.direction == 'inbound' ? AppColors.primary : AppColors.sage),
    )),
  );

  Widget _aiBadge() => Container(
    margin: const EdgeInsets.only(right: 6),
    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
    decoration: BoxDecoration(
      color: AppColors.sage.withOpacity(0.1),
      borderRadius: BorderRadius.circular(4),
    ),
    child: Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(Icons.auto_awesome, size: 10, color: AppColors.sage),
      const SizedBox(width: 2),
      Text('AI', style: GoogleFonts.plusJakartaSans(fontSize: 8, fontWeight: FontWeight.w800, color: AppColors.sage)),
    ]),
  );

  Widget _unreadCount(int count) => Container(
    padding: const EdgeInsets.all(8),
    decoration: BoxDecoration(color: AppColors.surface2, shape: BoxShape.circle),
    child: Text('$count', style: GoogleFonts.plusJakartaSans(fontSize: 10, fontWeight: FontWeight.w700, color: AppColors.textSec)),
  );

  Widget _buildEmptyState() => Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
    Icon(Icons.chat_bubble_outline_rounded, size: 48, color: AppColors.textMuted),
    const SizedBox(height: 16),
    Text('Inbox Clear', style: GoogleFonts.plusJakartaSans(color: AppColors.textSec, fontWeight: FontWeight.w700)),
  ]));

  void _navigateToDetail(_ChatThread thread) {
    final id = thread.customerId ?? thread.phoneNumber!;
    Navigator.push(context, MaterialPageRoute(
        builder: (_) => ConversationDetailScreen(
          customerId: id,
          customerName: thread.customerName ?? id,
          preferredCountry: thread.preferredCountry,
        ),
    ));
  }

  String _formatTime(DateTime dt) {
    final now = DateTime.now();
    final diff = now.difference(dt);
    if (diff.inMinutes < 60) return '${diff.inMinutes}m';
    if (diff.inHours < 24) return '${diff.inHours}h';
    return DateFormat('dd/MM').format(dt);
  }
}

class _ChatThread {
  String? customerId;
  String? phoneNumber;
  String? customerName;
  String? preferredCountry;
  Conversation lastMessage;
  int messageCount;
  int inboundCount;

  _ChatThread({
    this.customerId,
    this.phoneNumber,
    this.customerName,
    this.preferredCountry,
    required this.lastMessage,
    required this.messageCount,
    required this.inboundCount,
  });
}
