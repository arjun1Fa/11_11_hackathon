import 'package:supabase/supabase.dart';
import 'lib/models/customer.dart';
import 'lib/models/conversation.dart';

void main() async {
  final supabase = SupabaseClient(
    'https://yoirzyoeshlyqxilpygm.supabase.co',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvaXJ6eW9lc2hseXF4aWxweWdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU5MDg0ODksImV4cCI6MjA5MTQ4NDQ4OX0.YVsvtMx4dAIl3PhHLa6MOI1qMmhpXq-XeMuwKLMJOQM',
  );
  try {
    final res = await supabase.from('conversations').select('*, customers(name, preferred_country)');
    final list = (res as List).map((r) => Conversation.fromJson(r)).toList();
    print('Conversations mapped successfully: ${list.length}');
  } catch(e, s) { print('CONV ERR: $e\n$s'); }
  try {
    final res = await supabase.from('customers').select();
    final list = (res as List).map((r) => Customer.fromJson(r)).toList();
    print('Customers mapped successfully: ${list.length}');
  } catch(e, s) { print('CUST ERR: $e\n$s'); }
}
