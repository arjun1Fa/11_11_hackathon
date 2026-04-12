import 'package:supabase_flutter/supabase_flutter.dart';
import 'dart:io';

void main() async {
  print('--- Supabase Force Injection ---');
  
  final supabase = SupabaseClient(
    'https://yoirzyoeshlyqxilpygm.supabase.co',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvaXJ6eW9lc2hseXF4aWxweWdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU5MDg0ODksImV4cCI6MjA5MTQ4NDQ4OX0.YVsvtMx4dAIl3PhHLa6MOI1qMmhpXq-XeMuwKLMJOQM',
  );

  try {
    print('Attempting combined injection...');
    
    // 1. Try to insert into the queue first
    try {
      await supabase.from('handoff_queue').insert({
        'customer_id': '923f1c74-fdd5-4447-a7aa-fc9f1c78a238',
        'reason': 'URGENT: Manual Verification Test',
        'status': 'pending'
      });
      print('Queue entry created!');
    } catch(e) {
      print('Queue entry FAILED (likely RLS): $e');
    }

    // 2. Update the customer flag
    await supabase.from('customers').update({
       'is_handoff_active': true,
       'appointment_requested': true 
    }).eq('id', '923f1c74-fdd5-4447-a7aa-fc9f1c78a238');
    
    print('Customer flag updated!');
    
    // 3. Check persistence
    final res = await supabase.from('customers').select().eq('id', '923f1c74-fdd5-4447-a7aa-fc9f1c78a238').single();
    print('Immediate Verification - is_handoff_active: ${res['is_handoff_active']}');

  } catch(e) { 
    print('GLOBAL FAILED: $e'); 
  }

  exit(0);
}
