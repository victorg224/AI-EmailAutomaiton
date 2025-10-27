from app import app, db
from models import EmailTemplate

def add_8a_template():
    with app.app_context():
        template = EmailTemplate(
            name="8(a) Partnership Outreach",
            description="Template for reaching out to other 8(a) companies for potential partnerships and sole source opportunities.",
            template_content="""Subject: 8(a) Partnership Opportunity - GSA IT Schedule 70 Collaboration

Dear {person_name},

I noticed Enspyre Management Services' GSA IT Schedule 70 contract (SIN 54151S) and your impressive range of NAICS codes, particularly in {aligned_naics} which aligns with our core capabilities. Congratulations on your recent achievements and growing presence in the federal space.

As a fellow 8(a) certified company, {our_company_name} sees significant potential for collaboration, especially given your UEI: RZAKC9KNLF89 and established presence in IT Professional Services. Our capabilities complement your service offerings in:

- {matching_naics_1} 
- {matching_naics_2}
- {matching_naics_3}

Key differentiators about {our_company_name}:
- {certification_1}
- {certification_2}
- {past_performance_highlight}
- {unique_capability}

Given your strong presence in both IT and Project Management services, I believe we could explore teaming opportunities that leverage both our GSA schedules and 8(a) status for upcoming federal opportunities.

Would you be open to a brief 15-minute call next week to discuss potential collaboration? I'd like to share specific ways we could support your work in {specific_service_area} and explore joint pursuit of sole source opportunities.

Best regards,
{sender_name}
{sender_title}
{our_company_name}
{contact_info}

P.S. For immediate reference, our capability statement is available at {website_url}""",
            variables_guide="""Available variables:
{person_name} - Contact person's name
{our_company_name} - Your company name
{aligned_naics} - NAICS codes that align with target company
{matching_naics_1} - First matching NAICS code and description
{matching_naics_2} - Second matching NAICS code and description
{matching_naics_3} - Third matching NAICS code and description
{certification_1} - Your first key certification
{certification_2} - Your second key certification
{past_performance_highlight} - Key past performance
{unique_capability} - Your unique capability
{specific_service_area} - Specific service area for collaboration
{sender_name} - Your name
{sender_title} - Your title
{contact_info} - Your contact information
{website_url} - Your website URL"""
        )
        
        db.session.add(template)
        db.session.commit()
        print("8(a) template added successfully!")

def add_cybersecurity_template():
    """Add the Cybersecurity Threat Detection & Response Automation outreach template to the database with variables for context-specific parts."""
    template_content = '''
Hi {recipient_name},

I'm reaching out in response to the {contract_type} contract opportunity. My name is Victor Gandara, and I represent Enspyre Management Services, a certified small business specializing in AI automation, cybersecurity, and intelligent IT systems.

We deliver secure, scalable solutions that align with your project's goals, including:

- AI-powered threat detection & response using behavioral analytics and anomaly detection
- Seamless integration with SIEM, firewalls, and endpoint protection platforms
- Automated alert tuning, prioritization, and real-time reporting
- Robust data compliance and support for secure system deployment
- Ongoing model optimization and technical support

We've attached our capabilities statement outlining our technical approach, certifications (including SIN 54151S), and relevant NAICS codes. Our team is agile, experienced, and committed to supporting initiatives that demand both speed and security.

I'd appreciate the opportunity to speak further and explore how we can support your team in delivering this project successfully.
'''
    template = EmailTemplate(
        name='Cybersecurity Threat Detection Outreach',
        description='Outreach for cybersecurity/automation contracts, context-adapted',
        template_content=template_content
    )
    db.session.add(template)
    db.session.commit()
    print('Cybersecurity outreach template added.')

if __name__ == "__main__":
    add_8a_template() 