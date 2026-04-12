import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../models/conversation.dart';
import '../services/supabase_service.dart';




class ConversationTile extends StatefulWidget {
  final Conversation conversation;
  final bool highlighted;

  const ConversationTile({super.key, required this.conversation, this.highlighted = false});

  @override
  State<ConversationTile> createState() => _ConversationTileState();
}

class _ConversationTileState extends State<ConversationTile> {
  bool _isExpanded = false;
  List<Conversation> _fullHistory = [];
  bool _isLoadingHistory = false;

  void _toggleExpand() async {
    setState(() => _isExpanded = !_isExpanded);
    if (_isExpanded && _fullHistory.isEmpty) {
      await _fetchHistory();
    }
  }

  Future<void> _fetchHistory() async {
    setState(() => _isLoadingHistory = true);
    try {
      if (widget.conversation.customerId == null) {
        if (mounted) setState(() { _fullHistory = [widget.conversation]; _isLoadingHistory = false; });
        return;
      }
      final svc = context.read<SupabaseService>();
      final messages = await svc.getConversationsForCustomer(widget.conversation.customerId!);
      if (mounted) setState(() { _fullHistory = messages; _isLoadingHistory = false; });
    } catch (_) { if (mounted) setState(() => _isLoadingHistory = false); }
  }

  @override
  Widget build(BuildContext context) {
    final conversation = widget.conversation;
    final preview = conversation.messageText.length > 50
        ? '${conversation.messageText.substring(0, 50)}...'
        : conversation.messageText;

    return Theme(
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: ExpansionTile(
        onExpansionChanged: (_) => _toggleExpand(),
        tilePadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        leading: Container(
          width: 36, height: 36,
          decoration: BoxDecoration(
            color: widget.highlighted ? AppColors.primary : AppColors.primaryDim,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Center(
            child: Text(
              conversation.customerName?.isNotEmpty == true
                  ? conversation.customerName![0].toUpperCase() : '?',
              style: GoogleFonts.outfit(
                  color: widget.highlighted ? Colors.white : AppColors.primary, 
                  fontWeight: FontWeight.w800),
            ),
          ),
        ),
        title: Row(
          children: [
            Text(conversation.countryFlag, style: const TextStyle(fontSize: 14)),
            const SizedBox(width: 6),
            Expanded(
              child: Text(conversation.customerName ?? 'Unknown',
                style: GoogleFonts.outfit(
                    fontWeight: FontWeight.w700, fontSize: 14, color: AppColors.textPri)),
            ),
            Text(DateFormat('HH:mm').format(conversation.timestamp),
              style: GoogleFonts.outfit(fontSize: 10, color: AppColors.textMuted)),
          ],
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 4),
          child: Row(
            children: [
              Expanded(
                child: Text(preview, 
                  style: GoogleFonts.outfit(fontSize: 12, color: AppColors.textSec),
                  maxLines: 1, overflow: TextOverflow.ellipsis),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.primaryDim,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(_isExpanded ? 'CLOSE' : 'VIEW CHAT', 
                      style: GoogleFonts.outfit(fontSize: 8, fontWeight: FontWeight.w800, color: AppColors.primary)),
                    const SizedBox(width: 2),
                    Icon(_isExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down, 
                      size: 10, color: AppColors.primary),
                  ],
                ),
              ),
            ],
          ),
        ),
        children: [
          if (_isLoadingHistory)
            const Padding(
              padding: EdgeInsets.all(16.0),
              child: Center(child: SizedBox(width: 20, height: 20, 
                child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary))),
            )
          else ...[
            _groupSection('Student Queries', 'inbound', Icons.person_pin_circle_outlined, AppColors.primary),
            _groupSection('Business Responses', 'outbound', Icons.smart_toy_outlined, AppColors.sage),
            const SizedBox(height: 12),
          ],
        ],
      ),
    );
  }

  Widget _groupSection(String title, String direction, IconData icon, Color color) {
    final msgs = _fullHistory.where((m) => m.direction == direction).toList();
    if (msgs.isEmpty) return const SizedBox();

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surface2, // Glassy inset
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3), width: 1.0),
        boxShadow: [
          BoxShadow(color: color.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 0)),
          BoxShadow(color: Colors.black.withOpacity(0.2), blurRadius: 4, offset: const Offset(0, 2)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(color: color.withOpacity(0.1), shape: BoxShape.circle),
                child: Icon(icon, size: 12, color: color),
              ),
              const SizedBox(width: 8),
              Text(title.toUpperCase(), style: GoogleFonts.outfit(
                  fontSize: 11, fontWeight: FontWeight.w800, color: color, letterSpacing: 1.0)),
              const Spacer(),
              Text('${msgs.length} msg', style: GoogleFonts.outfit(fontSize: 9, color: AppColors.textMuted)),
            ],
          ),
          const SizedBox(height: 10),
          ...msgs.take(8).map((m) => _messageEntry(m)), 
          if (msgs.length > 8)
            Padding(
              padding: const EdgeInsets.only(left: 10, top: 4),
              child: Text('+ ${msgs.length - 8} more messages', 
                style: GoogleFonts.outfit(fontSize: 10, color: AppColors.textMuted, fontStyle: FontStyle.italic)),
            ),
        ],
      ),
    );
  }

  Widget _messageEntry(Conversation msg) {
    return Container(
      margin: const EdgeInsets.only(bottom: 4, left: 6),
      padding: const EdgeInsets.only(left: 10),
      decoration: const BoxDecoration(border: Border(left: BorderSide(color: AppColors.border, width: 1.5))),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(msg.messageText, 
            style: GoogleFonts.outfit(fontSize: 12, height: 1.4, color: AppColors.textPri)),
          Text(DateFormat('MMM dd, HH:mm').format(msg.timestamp), 
            style: GoogleFonts.outfit(fontSize: 9, color: AppColors.textMuted)),
        ],
      ),
    );
  }
}
