import 'package:supabase/supabase.dart';
void main() async {
  final client = SupabaseClient('https://yoirzyoeshlyqxilpygm.supabase.co', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvaXJ6eW9lc2hseXF4aWxweWdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU5MDg0ODksImV4cCI6MjA5MTQ4NDQ4OX0.YVsvtMx4dAIl3PhHLa6MOI1qMmhpXq-XeMuwKLMJOQM');
  final res = await client.from('conversations').select('id, customers(name)');
  print(res.take(5).toList());
}
