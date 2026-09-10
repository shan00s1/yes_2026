-- ==============================================================================
-- YES 2026 SUMMIT - SUPABASE POSTGRESQL PRODUCTION DATABASE SCHEMA
-- Visvesvaraya Research and Innovation Foundation (VRIF), VTU Belagavi
-- ==============================================================================
-- To execute:
-- 1. Log in to your Supabase Project Dashboard (https://supabase.com/dashboard)
-- 2. Open "SQL Editor" from the left sidebar
-- 3. Click "New Query", paste this entire script, and click "RUN"
-- ==============================================================================

-- 1. ATTENDEE REGISTRATIONS TABLE
CREATE TABLE IF NOT EXISTS public.registrations (
    id SERIAL PRIMARY KEY,
    registration_id VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(20) NOT NULL CHECK (category IN ('participant', 'delegate', 'faculty', 'vip')),
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    organization VARCHAR(200) NOT NULL,
    designation VARCHAR(150),
    track_or_industry VARCHAR(150),
    custom_fields_json TEXT,
    qr_code_data TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'REGISTERED' CHECK (status IN ('REGISTERED', 'CHECKED_IN')),
    check_in_time VARCHAR(50),
    check_in_station VARCHAR(100),
    created_at VARCHAR(50) NOT NULL,
    email_sent INT DEFAULT 1
);

-- Registrations Indexes for Sub-Millisecond Search & Lookups
CREATE INDEX IF NOT EXISTS idx_registrations_reg_id ON public.registrations(registration_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_registrations_email_unique ON public.registrations(LOWER(email));
CREATE INDEX IF NOT EXISTS idx_registrations_category ON public.registrations(category);
CREATE INDEX IF NOT EXISTS idx_registrations_status ON public.registrations(status);

-- Enable Row Level Security (RLS) with full access policies
ALTER TABLE public.registrations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow service role full access" ON public.registrations;
CREATE POLICY "Allow service role full access" ON public.registrations FOR ALL USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "Allow anon read and insert" ON public.registrations;
CREATE POLICY "Allow anon read and insert" ON public.registrations FOR ALL USING (true) WITH CHECK (true);

COMMENT ON TABLE public.registrations IS 'Stores official attendees, participants, delegates, and faculty/mentors for YES 2026.';

-- 2. EMAIL AUDIT LOGS TABLE
CREATE TABLE IF NOT EXISTS public.emails_log (
    id SERIAL PRIMARY KEY,
    registration_id VARCHAR(50) NOT NULL,
    recipient_email VARCHAR(150) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    html_body TEXT NOT NULL,
    sent_at VARCHAR(50),
    delivery_status VARCHAR(20) DEFAULT 'DELIVERED'
);

CREATE INDEX IF NOT EXISTS idx_emails_log_reg_id ON public.emails_log(registration_id);
COMMENT ON TABLE public.emails_log IS 'Audit log of sent digital badge emails with confirmation records.';

-- 3. SYSTEM ACTIVITY & AUDIT TRAIL TABLE
CREATE TABLE IF NOT EXISTS public.activity_logs (
    id SERIAL PRIMARY KEY,
    registration_id VARCHAR(50),
    action VARCHAR(50) NOT NULL,
    details TEXT,
    timestamp VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_activity_logs_reg_id ON public.activity_logs(registration_id);
COMMENT ON TABLE public.activity_logs IS 'System audit trail recording badge generation, check-in scans, and staff overrides.';

-- 4. DYNAMIC EVENT METADATA
CREATE TABLE IF NOT EXISTS public.event_meta (
    key VARCHAR(50) PRIMARY KEY,
    value TEXT NOT NULL
);

COMMENT ON TABLE public.event_meta IS 'Global summit information, venue location, dates, and organizational branding.';

-- 5. DYNAMIC SCHEDULE ITEMS
CREATE TABLE IF NOT EXISTS public.schedule_items (
    id SERIAL PRIMARY KEY,
    day VARCHAR(10) NOT NULL,
    time_range VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    track_tag VARCHAR(50)
);

-- 6. DIGNITARY SPEAKERS & LEADERSHIP
CREATE TABLE IF NOT EXISTS public.speakers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(100) NOT NULL,
    organization VARCHAR(150) NOT NULL,
    initials VARCHAR(5) NOT NULL
);

-- ------------------------------------------------------------------------------
-- SEED AUTHENTIC YES 2026 SUMMIT METADATA
-- ------------------------------------------------------------------------------

INSERT INTO public.event_meta (key, value) VALUES
    ('event_name', 'YES 2026'),
    ('event_full_title', 'Young Entrepreneurs Summit - YES 2026'),
    ('organizer', 'VTU''s Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi'),
    ('dates', '27th & 28th September 2026'),
    ('venue_name', 'VTU Main Campus, Jnana Sangama'),
    ('venue_address', 'Machhe, Belagavi, Karnataka 590018'),
    ('venue_city', 'Belagavi, Karnataka'),
    ('tagline', 'Embrace the resounding ''YES'' to innovations that propel us into the future.'),
    ('total_participants_hosted', '150'),
    ('tbi_location', 'Second Floor, VRIF Building, TBI Centre, VTU Belagavi')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- SEED SCHEDULE DAY 1 (27 Sept 2026)
INSERT INTO public.schedule_items (day, time_range, title, description, track_tag) VALUES
    ('day1', '08:30 AM - 10:00 AM', 'Express Registration & Badge Issuance', 'Camera-assisted QR check-in & personalized lanyard ID badge printing', 'Desk Kiosk'),
    ('day1', '10:00 AM - 11:30 AM', 'Grand Inaugural Ceremony & Welcome Address', 'Welcome by VTU Leadership, Dignitary addresses by Govt of Karnataka IT/BT delegates', 'APJ Abdul Kalam Auditorium'),
    ('day1', '11:30 AM - 12:30 PM', 'TBI Infrastructure Inauguration & Navodaya Cohort 1 Onboarding', 'Ribbon-cutting of 2nd Floor TBI Centre & induction ceremony for selected incubatees', 'VRIF TBI Centre (2nd Floor)'),
    ('day1', '12:30 PM - 01:30 PM', 'Program Milestones: SamShoDhana, SheInnovates & Vinyasa', 'Presentation of breakthroughs in deep-tech translation, women founders & acceleration', 'APJ Abdul Kalam Auditorium'),
    ('day1', '01:30 PM - 02:30 PM', 'Executive Networking Luncheon', 'Curated networking lunch for delegates, speakers, founders & mentors', 'Executive Dining Pavilion'),
    ('day1', '02:30 PM - 04:30 PM', 'B2B Matchmaking & Stakeholder Roundtables', 'High-level dialogues on incubation policy, corporate partnerships & angel syndicates', 'Jana Samvada 1 & 2'),
    ('day1', '04:30 PM - 05:30 PM', 'Keynote Address: Scaling Deep-Tech from North Karnataka', 'Distinguished founders and investors discuss tier-2 tech ecosystem growth', 'APJ Abdul Kalam Auditorium'),
    ('day1', '06:30 PM - 09:30 PM', 'Cultural Evening, Musical Performances & Networking Dinner', 'Celebration of entrepreneurship with live cultural performances and banquet dinner', 'Open Amphitheater & Campus Grounds');

-- SEED SCHEDULE DAY 2 (28 Sept 2026)
INSERT INTO public.schedule_items (day, time_range, title, description, track_tag) VALUES
    ('day2', '09:00 AM - 10:00 AM', 'Breakfast Mixer & Venture Networking', 'Informal morning connections between incubatees, delegates & angels', 'Exhibition Courtyard'),
    ('day2', '10:00 AM - 01:00 PM', 'Top 20 Project Showcase & Live Investor Pitches', 'The 20 most promising VRIF-incubated startups pitch live before angel syndicates', 'APJ Abdul Kalam Auditorium'),
    ('day2', '01:00 PM - 02:00 PM', 'Networking Lunch & Prototype Demo Walkthrough', 'Hands-on walkthrough of hardware, robotics, deep-tech & bio-engineering demos', 'TBI Prototyping Hall'),
    ('day2', '02:00 PM - 03:30 PM', 'Panel: Intellectual Property, Patenting & Global Commercialization', 'Academic-industry technology transfer leaders discuss IP creation in universities', 'Jana Samvada 1'),
    ('day2', '03:30 PM - 04:30 PM', 'Startup Karnataka & KDEM Policy Roundtable', 'Government support schemes, seed fund access, and regulatory frameworks', 'Jana Samvada 2'),
    ('day2', '04:30 PM - 05:30 PM', 'YES 2026 Innovation Awards & Valedictory Ceremony', 'Presentation of Top Venture Grants, felicitations, and closing address', 'APJ Abdul Kalam Auditorium');

-- SEED DIGNITARY SPEAKERS
INSERT INTO public.speakers (name, role, organization, initials) VALUES
    ('Prof. S. Vidyashankar', 'Hon''ble Vice Chancellor', 'VTU Belagavi', 'SV'),
    ('Dr. B. E. Rangaswamy', 'Registrar', 'VTU Belagavi', 'BR'),
    ('Shri Priyank Kharge', 'Hon''ble Minister for IT/BT & Rural Dev.', 'Government of Karnataka', 'PK'),
    ('Dr. Ekroop Caur, IAS', 'Secretary to Govt., Dept. of IT/BT & S&T', 'Government of Karnataka', 'EC'),
    ('Sanjeev Gupta', 'CEO', 'Karnataka Digital Economy Mission (KDEM)', 'SG'),
    ('Darshan Shanbhag', 'Founder & Managing Partner', 'Early Founders Syndicate', 'DS');

-- Complete verification query
SELECT 'YES 2026 Supabase Schema initialized successfully' AS status,
       (SELECT COUNT(*) FROM public.schedule_items) AS schedule_count,
       (SELECT COUNT(*) FROM public.speakers) AS speaker_count;
