import os
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def seed_packages():
    packages = [
        {
            "id": "pkg_germany_001",
            "country": "Germany",
            "package_name": "Germany Public University Starter Package",
            "overview": "Designed for students who want world-class education at near-zero tuition. Provides end-to-end support for public university applications.",
            "tuition_fee": "0 – 1,500 EUR per year (semester admin fee)",
            "living_cost": "850 – 1,200 EUR per month",
            "duration": "3–4 years (Bachelor's) / 2 years (Master's)",
            "universities": ["TUM", "RWTH Aachen", "University of Stuttgart", "Heidelberg University", "Freie Universitat Berlin"],
            "services_included": ["University shortlisting", "Application assistance", "SOP/LOR guidance", "Blocked account support", "APS guidance", "Visa review"],
            "visa_support": "Full guidance: blocked account setup, APS certificate, embassy documentation",
            "scholarships": "DAAD, Deutschlandstipendium, University waivers",
            "intake_months": ["September/October", "March/April"],
            "eligibility": "Min 70% previous education, IELTS 6.5+"
        },
        {
            "id": "pkg_france_001",
            "country": "France",
            "package_name": "France Business School Premium Package",
            "overview": "Targeting elite Grande Ecoles and top-ranked business schools. Personalized support for MBA and MSc Finance/Marketing/Management.",
            "tuition_fee": "8,000 – 20,000 EUR per year",
            "living_cost": "900 – 1,400 EUR per month (Paris higher)",
            "duration": "1–2 years (Master's / MBA)",
            "universities": ["HEC Paris", "ESSEC", "EDHEC", "INSEAD", "Sciences Po Paris", "EM Lyon"],
            "services_included": ["Profile evaluation", "GMAT strategy", "Essay/SOP writing", "Interview coaching", "Campus France registration", "Accommodation search"],
            "visa_support": "Campus France registration, VFS appointment, visa interview preparation",
            "scholarships": "Eiffel Excellence, School merit scholarships, MOPGA grants",
            "intake_months": ["September", "January"],
            "eligibility": "Bachelor's degree, GMAT 690+ / IELTS 6.5+"
        },
        {
            "id": "pkg_netherlands_001",
            "country": "Netherlands",
            "package_name": "Netherlands Tech & Innovation Package",
            "overview": "Focus on technology, data science, and AI. Dutch universities have strong ties with global tech companies like ASML and Philips.",
            "tuition_fee": "6,000 – 15,000 EUR per year (Statutory ~2,314 EUR)",
            "living_cost": "900 – 1,300 EUR per month",
            "duration": "2 years (Master's) / 3 years (Bachelor's)",
            "universities": ["TU Delft", "UvA", "Eindhoven University", "Groningen", "Vrije Universiteit Amsterdam"],
            "services_included": ["Course matching", "Full processing", "CV/SOP support", "MVV visa support", "IND residence guidance", "Holland Scholarship help"],
            "visa_support": "MVV application, IND residence permit, DigiD registration",
            "scholarships": "Holland Scholarship (€5,000), Orange Tulip, TU Delft Excellence",
            "intake_months": ["September", "February"],
            "eligibility": "Relevant bachelor's field, IELTS 6.5+/7.0, Portfolio"
        }
    ]

    for pkg in packages:
        # Upsert based on ID
        res = supabase.table("packages").upsert(pkg).execute()
        print(f"Upserted package: {pkg['id']}")

def seed_knowledge_base():
    facts = [
        # Germany
        {"package_id": "pkg_germany_001", "country": "Germany", "category": "tuition", "title": "Germany Tuition Fees", "content": "Public universities in Germany charge 0 to 1,500 EUR per year. Most public universities charge only a semester admin fee."},
        {"package_id": "pkg_germany_001", "country": "Germany", "category": "visa", "title": "Germany Blocked Account", "content": "Students applying for a German student visa must open a blocked account with approximately 11,208 EUR (as of 2024)."},
        {"package_id": "pkg_germany_001", "country": "Germany", "category": "visa", "title": "Germany APS Certificate", "content": "Indian students applying to German universities must obtain an APS (Academic Evaluation Centre) certificate, which takes 4-6 weeks."},
        {"package_id": "pkg_germany_001", "country": "Germany", "category": "scholarships", "title": "DAAD Scholarship Germany", "content": "The DAAD (German Academic Exchange Service) offers many scholarships for international students based on merit and field."},
        {"package_id": "pkg_germany_001", "country": "Germany", "category": "living", "title": "Germany Living Costs", "content": "Students in Germany spend 850 to 1,200 EUR per month. Rent is typically the largest expense, ranging from 300 to 600 EUR."},
        {"package_id": "pkg_germany_001", "country": "Germany", "category": "eligibility", "title": "Germany Eligibility", "content": "Applicants usually need a minimum of 70% in previous education and an IELTS score of 6.5 or equivalent."},
        {"package_id": "pkg_germany_001", "country": "Germany", "category": "intake", "title": "Germany Intake Dates", "content": "Germany has two main intakes: Winter (Sep/Oct) and Summer (Mar/Apr). Winter is the primary intake."},
        {"package_id": "pkg_germany_001", "country": "Germany", "category": "faq", "title": "Germany Part-time Work", "content": "International students in Germany can work up to 120 full days or 240 half days per year."},
        
        # France
        {"package_id": "pkg_france_001", "country": "France", "category": "tuition", "title": "France Business School Tuition", "content": "Top French business schools charge 8,000 to 20,000 EUR per year depending on the program and school."},
        {"package_id": "pkg_france_001", "country": "France", "category": "scholarships", "title": "Eiffel Excellence Scholarship", "content": "The Eiffel Excellence Scholarship covers tuition and provides a monthly allowance for top international students in France."},
        {"package_id": "pkg_france_001", "country": "France", "category": "visa", "title": "France Campus France Process", "content": "All students from most countries must register on Campus France before applying for a student visa."},
        {"package_id": "pkg_france_001", "country": "France", "category": "living", "title": "France Living Costs", "content": "Monthly living costs in France range from 900 to 1,400 EUR. Paris is significantly more expensive at 1,200+ EUR."},
        {"package_id": "pkg_france_001", "country": "France", "category": "eligibility", "title": "France Eligibility", "content": "Requirements include a Bachelor's degree, IELTS 6.5+, and GMAT is highly recommended (690+ for top schools)."},
        {"package_id": "pkg_france_001", "country": "France", "category": "eligibility", "title": "France IELTS Requirement", "content": "The minimum required IELTS score for French Business Schools and Universities is 6.5. Top-tier Grande Écoles may require a 7.0 or higher."},
        {"package_id": "pkg_france_001", "country": "France", "category": "faq", "title": "France Work Rules", "content": "International students in France may work up to 964 hours per year (approx 20 hours/week)."},
        {"package_id": "pkg_france_001", "country": "France", "category": "faq", "title": "Is French Language Required", "content": "Most top business school programs are fully in English, but basic French is helpful for daily life."},

        # Netherlands
        {"package_id": "pkg_netherlands_001", "country": "Netherlands", "category": "tuition", "title": "Netherlands Tuition Fees", "content": "Tuition for non-EEA международный students in the Netherlands ranges from 6,000 to 15,000 EUR per year."},
        {"package_id": "pkg_netherlands_001", "country": "Netherlands", "category": "scholarships", "title": "Holland Scholarship", "content": "The Holland Scholarship is a one-time grant of €5,000 for non-EEA students in their first year."},
        {"package_id": "pkg_netherlands_001", "country": "Netherlands", "category": "visa", "title": "Netherlands MVV Residence Permit", "content": "Non-EEA students need an MVV (provisional residence permit) to enter the Netherlands for stays over 90 days."},
        {"package_id": "pkg_netherlands_001", "country": "Netherlands", "category": "eligibility", "title": "Netherlands Eligibility", "content": "Applicants need a relevant Bachelor's degree, an IELTS score of 6.5 or 7.0 for top research universities, and a portfolio for design/tech courses."},
        {"package_id": "pkg_netherlands_001", "country": "Netherlands", "category": "eligibility", "title": "Netherlands IELTS Requirement", "content": "Standard IELTS requirement is 6.5 for most programs. Some high-ranking programs at TU Delft or Eindhoven may require 7.0."},
        {"package_id": "pkg_netherlands_001", "country": "Netherlands", "category": "living", "title": "Netherlands Living Costs", "content": "Living costs in the Netherlands range from 900 to 1,300 EUR per month. Housing is the biggest challenge."},
        {"package_id": "pkg_netherlands_001", "country": "Netherlands", "category": "faq", "title": "Netherlands Post-Study Visa", "content": "The Netherlands offers an Orientation Year Permit (Zoekjaar) allowing graduates 1 year to find a job."},
        {"package_id": "pkg_netherlands_001", "country": "Netherlands", "category": "faq", "title": "Netherlands Housing Challenge", "content": "The housing market in NL is very competitive. Students are advised to apply for housing as soon as they receive an offer."},
        
        # General
        {"package_id": None, "country": "General", "category": "eligibility", "title": "IELTS Score Comparison", "content": "Germany usually requires 6.5. France Business schools require 6.5 to 7.0. Netherlands research universities often require 6.5 or 7.0."},
        {"package_id": None, "country": "General", "category": "faq", "title": "Choosing Between DE FR NL", "content": "Germany is best for low cost and STEM. France suits business students. Netherlands is great for tech and innovation."},
        {"package_id": None, "country": "General", "category": "faq", "title": "Work While Studying", "content": "All three countries allow part-time work, but limits vary (120 days in DE, 964 hours in FR, 16 hours in NL)."}
    ]

    for fact in facts:
        # Upsert based on title (which is now UNIQUE)
        res = supabase.table("knowledge_base").upsert(fact, on_conflict="title").execute()
        print(f"Upserted fact: {fact['title']}")

def seed_demo_customers():
    # Business ID (placeholder)
    biz_id = str(uuid.uuid4())
    print(f"Using demo business_id: {biz_id}")

    customers = [
        {
            "phone_number": "+919876543210",
            "name": "Priya Nair",
            "language": "ml",
            "preferred_country": "Germany",
            "interested_package_id": "pkg_germany_001",
            "education_level": "Masters",
            "field_of_study": "Computer Science",
            "ielts_score": 6.5,
            "category": "At Risk",
            "churn_score": 0.8,
            "business_id": biz_id
        },
        {
            "phone_number": "+919000000001",
            "name": "Arjun Mehta",
            "language": "en",
            "preferred_country": "France",
            "interested_package_id": "pkg_france_001",
            "education_level": "MBA",
            "field_of_study": "Business",
            "ielts_score": 7.0,
            "category": "Champion",
            "churn_score": 0.2,
            "business_id": biz_id
        },
        {
            "phone_number": "+919000000002",
            "name": "Meena Pillai",
            "language": "ta",
            "preferred_country": "Netherlands",
            "interested_package_id": "pkg_netherlands_001",
            "education_level": "Masters",
            "field_of_study": "Data Science",
            "ielts_score": 6.5,
            "category": "Lost",
            "churn_score": 0.9,
            "business_id": biz_id
        },
        {
            "phone_number": "+919000000003",
            "name": "Rahul Varma",
            "language": "hi",
            "preferred_country": "Germany",
            "interested_package_id": "pkg_germany_001",
            "education_level": "Bachelors",
            "field_of_study": "Mechanical Engineering",
            "ielts_score": 6.0,
            "category": "At Risk",
            "churn_score": 0.75,
            "business_id": biz_id
        }
    ]

    for cust in customers:
        res = supabase.table("customers").upsert(cust, on_conflict="phone_number").execute()
        print(f"Upserted customer: {cust['name']}")

def seed_interactions():
    print("Seeding Interactions for Dashboard...")
    # Get Customer IDs
    res = supabase.table("customers").select("id, name").execute()
    cust_map = {c['name']: c['id'] for c in res.data}
    
    # Conversations (Today)
    convo_data = [
        # Priya (At Risk) - some messages today
        {"customer_id": cust_map["Priya Nair"], "direction": "inbound", "message_text": "Is there any scholarship for Germany?", "intent_label": "scholarship_query", "action_taken": "auto_reply"},
        {"customer_id": cust_map["Priya Nair"], "direction": "outbound", "message_text": "Yes, DAAD is the primary one. Would you like details?", "intent_label": "scholarship_query", "action_taken": "auto_reply"},
        # Arjun (Champion)
        {"customer_id": cust_map["Arjun Mehta"], "direction": "inbound", "message_text": "When is the next intake for France?", "intent_label": "enquiry", "action_taken": "auto_reply"},
        {"customer_id": cust_map["Arjun Mehta"], "direction": "outbound", "message_text": "January is the next major intake. We can start your application now.", "intent_label": "enquiry", "action_taken": "auto_reply"},
        # Meena (Lost)
        {"customer_id": cust_map["Meena Pillai"], "direction": "inbound", "message_text": "I am looking for Netherlands visa info.", "intent_label": "visa_question", "action_taken": "auto_reply"},
    ]
    
    # Bulk insert conversations
    supabase.table("conversations").insert(convo_data).execute()
    print(f"Seeded {len(convo_data)} conversations.")

    # Enquiry Events (Today - Converted)
    enquiry_data = [
        {"customer_id": cust_map["Arjun Mehta"], "country": "France", "package_id": "pkg_france_001", "status": "converted", "notes": "Student paid registration fee."},
    ]
    supabase.table("enquiry_events").insert(enquiry_data).execute()
    print(f"Seeded {len(enquiry_data)} conversions.")

def run_seeding():
    print("Starting Seeding...")
    try:
        seed_packages()
        seed_knowledge_base()
        seed_demo_customers()
        seed_interactions()
        print("Seeding Completed Successfully!")
    except Exception as e:
        print(f"Seeding Failed: {e}")

if __name__ == "__main__":
    run_seeding()
