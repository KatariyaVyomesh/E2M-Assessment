import os
import json
import zlib
import base64
from openai import OpenAI
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure SambaNova API (OpenAI-compatible)
API_KEY = os.getenv("SAMBANOVA_API_KEY")
client = None
if API_KEY:
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://api.sambanova.ai/v1",
    )

def home(request):
    """
    Clears all existing audit data from the session to ensure privacy
    and force a fresh analysis for the next candidate.
    """
    keys_to_clear = ["analysis_report", "resume_text", "job_description"]
    for key in keys_to_clear:
        if key in request.session:
            del request.session[key]
    return render(request, "home.html")

def analyze_with_sambanova(resume_text, job_description="", analysis_type="deep"):
    """
    Analyzes resume and JD using SambaNova (DeepSeek-V3.2) with multi-input validation.
    """
    if not API_KEY:
        return {"error": "SambaNova API Key not configured."}

    # Define Focal Instructions based on Analysis Type
    focus_map = {
        "executive": "Focus: EXECUTIVE SUMMARY. Concise rationale, high-level verdict. Limit lists.",
        "quick": "Focus: RAPID SCREENING. Highlight skills and relevance match score.",
        "deep": "Focus: FULL DEEP DIVE. Comprehensive 13-metric recruitment report."
    }
    focus_instr = focus_map.get(analysis_type, focus_map["deep"])

    try:
        # Optimized Telegraphic Prompt with Multi-Input Validation
        # Truncate inputs to keep within speed limits (Vercel timeout)
        resume_text_trunc = resume_text[:15000] 
        jd_text_trunc = job_description[:10000]

        prompt = f"""
        Role: Hiring Analyst. Task: Validate & Analyze. {focus_instr}
        
        VALIDATION RULES:
        1. Resume: 3+ signals (Skills, Exp, Edu, Projects, Contact).
        2. JD: 2+ signals (Job Title, Requirements, Responsibilities, Skills).

        Fail output examples:
        {{"is_valid_resume":false,"is_valid_jd":true,"message":"Invalid Resume: Please provide a valid CV text."}}
        {{"is_valid_resume":true,"is_valid_jd":false,"message":"Invalid Job Profile: Please provide a valid job description."}}

        Input: 
        Resume: {resume_text_trunc}
        JD: {jd_text_trunc}

        Success output (Minified JSON ONLY):
        {{"is_valid_resume":true,"is_valid_jd":true,"detected_role":"","confidence_score":0,"experience_analysis":{{"level":"Fresher/Junior/Mid/Senior","total_years":0,"relevant_years":0}},"skill_ecosystem":{{"technical":[{{"skill":"","proficiency":"Advanced/Intermediate/Beginner"}}],"tools":[{{"skill":"","proficiency":""}}],"soft":[]}},"relevance_match":0,"keyword_analysis":{{"matched":[],"missing":[]}},"relevant_projects":[{{"name":"","duration":"E.g. 6 Months OR Jan 23 - Present","relevance":"High/Medium/Low/No"}}, "(Repeat for EVERY project found)"],"relevant_certifications":[{{"name":"","issuing_org":"","relevance":"High/Medium/Low/No"}}, "(Repeat for EVERY certificate found)"],"achievements":[{{ "text":"","relevance":"High/Medium/Low/No" }}, "(Repeat for EVERY achievement found)"],"key_differentiators":[],"capability_gaps":[],"suggestions_for_improvement":[],"domain_expertise":"","candidate_score":0,"hireability_tag":"Hire Immediately / Consider / Reject","final_ai_result":"Short 1-sentence summary","explanation":"Detailed 3-sentence explanation of the match score, matched/missing skills, and hiring verdict"}}
        """
        
        response = client.chat.completions.create(
            model="DeepSeek-V3.2",
            messages=[
                {"role": "system", "content": """Assistant: Advanced Recruitment AI.
                STRICT EVALUATION & EXTRACTION AUDIT RULES:
                1. ZERO FILTER POLICY: Extract EVERY single project, certification, and achievement found in the resume. 
                2. 1:1 DATA MAPPING: If there are 10 certs, you MUST return 10 certs. If there are 8 achievements, return 8. DO NOT skip, merge, or filter ANY data.
                3. RELEVANCE LABELING: Use the 'relevance' field to indicate fit (High/Medium/Low/No Match) against the JD, but NEVER omit an item because it doesn't match.
                4. PRIMARY TARGET: The Job Description is for SCORING, not for FILTERING. List all data first, then score it.
                5. ROLE FIDELITY: Reflect mismatches in the relevance field. (e.g., Backend applying for AI/ML should show 'Low' relevance for Backend projects).
                6. ZERO SUMMARIZATION: Capture specific names and details accurately.
                7. JSON INTEGRITY: Output strictly valid minified JSON. Ensure every quote is closed and any truncation is a failure.
"""},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            stream=False,
            max_tokens=4096,
            response_format={ "type": "json_object" }
        )
        
        raw_text = response.choices[0].message.content.strip()
        print(f"DEBUG: AI Raw Response: {raw_text}")
        
        if not raw_text:
            return {"error": "Empty response from SambaNova AI."}

        # Cleanup and ensure JSON extraction (Handle potential <think> tags from DeepSeek)
        import re
        text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
        if "```json" in text:
            text = text.split("```json")[-1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[-1].split("```")[0]
        
        text = text.strip()
        if not text.startswith('{'):
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                text = text[start:end+1]
        
        try:
            data = json.loads(text)
            
            # Post-processing: Auto-scale decimal scores to percentages
            score_keys = ['confidence_score', 'relevance_match', 'candidate_score']
            for key in score_keys:
                if key in data and isinstance(data[key], (int, float)):
                    if 0 < data[key] <= 1.0:
                        data[key] = int(data[key] * 100)
                    else:
                        data[key] = int(data[key])
            
            return data
            
        except json.JSONDecodeError as e:
            return {"error": f"JSON Parsing Error: {str(e)}", "raw_content": raw_text}

    except Exception as e:
        error_msg = str(e)
        if "rate_limit_exceeded" in error_msg.lower() or "429" in error_msg:
            return {"error": "AI server is currently busy (Rate Limit Exceeded). Please wait 10 minutes and try again."}
        elif "timeout" in error_msg.lower():
            return {"error": "Request timed out. Please try a shorter resume or wait a moment."}
        return {"error": f"SambaNova API Error: {error_msg}"}


def predict(request):
    if request.method == "POST":
        # Clear existing keys surgically for stability instead of a full flush
        keys_to_reset = ["analysis_report", "analysis_report_compressed", "resume_text", "job_description"]
        for key in keys_to_reset:
            if key in request.session:
                del request.session[key]

        resume_text = request.POST.get('resume_text', '')
        job_description = request.POST.get('job_description', '')
        analysis_type = request.POST.get('analysis_type', 'deep')

        print(f"DEBUG: Starting AI Analysis for {len(resume_text)} chars...")
        
        analysis = analyze_with_sambanova(resume_text, job_description, analysis_type)
        
        if "error" in analysis:
            print(f"DEBUG: AI Error: {analysis['error']}")
            return render(request, "home.html", {"error": analysis["error"], "resume_text": resume_text, "job_description": job_description})

        # Check for AI-driven validation failures
        is_valid_resume = analysis.get("is_valid_resume", True)
        is_valid_jd = analysis.get("is_valid_jd", True)
        validation_message = analysis.get("message", "Invalid input detected.")

        if not is_valid_resume or not is_valid_jd:
            print(f"DEBUG: Validation Failed - Resume: {is_valid_resume}, JD: {is_valid_jd}")
            return render(request, "home.html", {
                "error": validation_message, 
                "resume_text": resume_text, 
                "job_description": job_description
            })

        # Save to session as a backup for browser-refresh
        try:
            json_report = json.dumps(analysis)
            compressed = base64.b64encode(zlib.compress(json_report.encode())).decode()
            request.session["analysis_report_compressed"] = compressed
        except Exception as e:
            print(f"ERROR: Session compression failed: {e}")

        request.session["resume_text"] = resume_text
        request.session["job_description"] = job_description
        request.session["analysis_type"] = analysis_type
        request.session.modified = True
        request.session.save()
        
        # Prepare context for IMMEDIATE DIRECT RENDERING (bypasses 4KB cookie limit)
        analysis_type = request.session.get('analysis_type', 'deep')
        mode_map = {"executive": "Executive Summary", "quick": "Quick Skills Match", "deep": "Full Deep Dive"}
        mode_label = mode_map.get(analysis_type, "Full Analysis")

        print(f"DEBUG: Rendering Dashboard Directly...")
        return render(request, "results.html", {
            "analysis": analysis,
            "resume_text": resume_text,
            "job_description": job_description,
            "mode_label": mode_label,
        })
        
    return redirect('home')

@never_cache
def results(request):
    """
    Displays the fresh analysis. Redirects to home if no active 
    'analysis_report' is found in the current session.
    Handles decompression for large Vercel reports.
    """
    compressed = request.session.get("analysis_report_compressed")
    analysis = None
    
    if compressed:
        try:
            decompressed = zlib.decompress(base64.b64decode(compressed.encode())).decode()
            analysis = json.loads(decompressed)
        except Exception as e:
            print(f"ERROR: Decompression failed: {e}")

    # Fallback for local or uncompressed data
    if not analysis:
        analysis = request.session.get("analysis_report")
    
    job_description = request.session.get("job_description")
    resume_text = request.session.get("resume_text")
    
    if not analysis:
        return redirect("home")
        
    # Format a human-readable label for the UI
    analysis_type = request.session.get('analysis_type', 'deep')
    mode_map = {
        "executive": "Executive Summary",
        "quick": "Quick Skills Match",
        "deep": "Full Deep Dive"
    }
    mode_label = mode_map.get(analysis_type, "Full Analysis")
        
    return render(request, "results.html", {
        "analysis": analysis,
        "resume_text": request.session.get('resume_text', ""),
        "job_description": request.session.get('job_description', ""),
        "mode_label": mode_label,
    })
