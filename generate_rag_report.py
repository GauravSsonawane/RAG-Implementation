import asyncio
import os
from fpdf import FPDF
from orchestrator.rag_workflow import rag_workflow
from dotenv import load_dotenv

load_dotenv()

QUESTIONS = [
    "What are the key steps in the new meter application process?",
    "How can a customer file a billing dispute?",
    "What is the protocol for emergency gas leaks?",
    "List the available payment plans for financial assistance.",
    "What are the most frequently asked questions about customer service hours?",
    "What documentation is required for a commercial meter installation?",
    "How long does the billing dispute resolution typically take?",
    "Who should be contacted first in case of a power line failure?",
    "Are there specific eligibility criteria for the Low-Income Assistance Program?",
    "What is the procedure for updating customer contact information?"
]

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Industrial RAG Performance Report', 0, 1, 'C')
        self.ln(10)

    def chapter_title(self, num, label):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, f'Question {num}: {label}', 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, answer, sources):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, f"Answer: {answer}")
        self.ln(2)
        self.set_font('Arial', 'I', 10)
        self.multi_cell(0, 6, f"Sources: {', '.join(sources) if sources else 'None'}")
        self.ln(10)

async def run_report():
    pdf = PDF()
    pdf.add_page()
    
    print("🚀 Starting RAG Report Generation...")
    
    for i, q in enumerate(QUESTIONS, 1):
        print(f"[{i}/10] Querying: {q}")
        inputs = {"query": q, "messages": []}
        config = {"configurable": {"thread_id": f"report_session_{i}"}}
        
        try:
            result = await rag_workflow.ainvoke(inputs, config=config)
            answer = result.get("answer", "No answer generated.")
            sources = result.get("sources", [])
            
            # Clean sources path for better PDF readability
            clean_sources = [s.split('\\')[-1].split('/')[-1] for s in sources]
            
            pdf.chapter_title(i, q)
            pdf.chapter_body(answer, clean_sources)
            
        except Exception as e:
            print(f"Error on Q{i}: {e}")
            pdf.chapter_title(i, q)
            pdf.chapter_body(f"Error during generation: {e}", [])

    report_path = "rag_performance_report.pdf"
    pdf.output(report_path)
    print(f"✅ Report generated successfully: {os.path.abspath(report_path)}")

if __name__ == "__main__":
    asyncio.run(run_report())
