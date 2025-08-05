
import streamlit as st, sqlite3, pandas as pd
from core.statement_parser import ingest_statement
from core.categorizer import tag_business
from core.tax_optimizer import optimize
from core.stock_api import stock_api
from financial_advisor.analytics import financial_analytics
from core.api import query_open_webui, query_ollama
from core.ollama_client import ollama_client

# Add some missing imports/functions
def ingest(file_path):
    """Placeholder for document ingestion"""
    return []

def add(texts):
    """Placeholder for adding texts to vector store"""
    pass
import tempfile
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Financial Advisor Suite", layout="wide")
st.title("🏦 Personal Financial Advisor Suite")

# Initialize session state
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {}



tabs = st.tabs(["🤖 Smart Assistant", "💻 Cyber Code Helper", "📊 Tax Dashboard", "📈 Investments", "📊 Analytics"])

conn = sqlite3.connect("/app/data/finance.db", check_same_thread=False)

with tabs[0]:
    st.subheader("🤖 Smart Personal Assistant")
    
    # Document upload section
    with st.expander("📄 Upload Documents"):
        uploaded = st.file_uploader("Upload document (PDF, TXT, etc.)", key="doc")
        if uploaded:
            try:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(uploaded.getbuffer())
                    tmp_path = tmp.name
                
                with st.spinner("Processing document..."):
                    docs = ingest(tmp_path)
                    add([d.text for d in docs])
                    os.unlink(tmp_path)
                    st.success(f"✅ Document '{uploaded.name}' indexed successfully!")
                    logger.info(f"Document uploaded and indexed: {uploaded.name}")
            except Exception as e:
                st.error(f"❌ Error processing document: {str(e)}")
                logger.error(f"Document processing error: {str(e)}")
    
    # Ollama model management
    with st.expander("🤖 Ollama Model Management"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Available Models")
            if ollama_client.is_available():
                for model in ollama_client.available_models:
                    icon = "⭐" if model == ollama_client.default_model else "📦"
                    st.write(f"{icon} {model}")
                
                if ollama_client.default_model:
                    st.info(f"Default model: {ollama_client.default_model}")
            else:
                st.warning("No models available. Please pull some models first.")
                st.code("""
# In your terminal or Ollama container:
ollama pull llama3.2:latest
ollama pull phi3:latest
ollama pull gemma:latest
                """)
        
        with col2:
            st.subheader("🔄 Model Actions")
            
            if st.button("🔄 Refresh Model List"):
                ollama_client._check_connection()
                st.rerun()
            
            st.subheader("💡 Suggested Models")
            st.markdown("""
            **Recommended models to pull:**
            - `llama3.2:latest` - Latest Llama model (recommended)
            - `phi3:latest` - Microsoft's fast model
            - `gemma:latest` - Google's efficient model
            - `qwen:latest` - Alibaba's multilingual model
            
            **To pull a model, run in terminal:**
            ```bash
            docker exec test5_turborag_cag-ollama-1 ollama pull llama3.2:latest
            ```
            """)
    
    # Chat interface
    st.subheader("💬 Chat with Your Assistant")
    
    # User profile setup
    with st.expander("👤 User Profile (for personalization)"):
        col1, col2 = st.columns(2)
        with col1:
            risk_tolerance = st.selectbox("Risk Tolerance", ["Conservative", "Moderate", "Aggressive"])
            annual_income = st.number_input("Annual Income ($)", min_value=0, value=50000)
        with col2:
            age = st.number_input("Age", min_value=18, max_value=100, value=30)
            investment_goals = st.text_area("Investment Goals", "Long-term wealth building")
        
        if st.button("Update Profile"):
            st.session_state.user_profile = {
                "risk_tolerance": risk_tolerance.lower(),
                "annual_income": annual_income,
                "age": age,
                "investment_goals": investment_goals
            }
            # cag_engine.update_user_profile(st.session_state.user_profile)  # Feature not implemented yet
            st.success("Profile updated!")
    
    q = st.text_input("Ask me anything about your finances, investments, or uploaded documents:", 
                     placeholder="e.g., 'How much should I save for retirement?' or 'What's in my uploaded document?'")
    
    if q:
        try:
            with st.spinner("Thinking..."):
                response = query_ollama(prompt=q, model="llama3.2:latest")
                
                # Display response
                st.markdown("### 🤖 Assistant Response")
                st.write(response)
                    
        except Exception as e:
            st.error(f"❌ Error generating response: {str(e)}")
            logger.error(f"Chat error: {str(e)}")


with tabs[1]:
    st.subheader("💻 Cyber Code Helper")
    
    st.info("Got a question about cybersecurity, ethical hacking, or secure coding? Ask away!")
    
    # Chat interface for Cyber Code Helper
    cyber_q = st.text_area("Ask a cyber-related question:", 
                           placeholder="e.g., 'Write a Python script to check for open ports on a host' or 'Explain the MITRE ATT&CK framework.'")
    
    if st.button("Get Cyber Help"):
        if cyber_q:
            try:
                with st.spinner("Consulting with cyber expert..."):
                    response = query_ollama(prompt=cyber_q, model="llama3.2:latest")
                    
                    st.markdown("### 🤖 Cyber Assistant Response")
                    st.markdown(response)

            except Exception as e:
                st.error(f"❌ Error getting cyber help: {str(e)}")
                logger.error(f"Cyber help error: {str(e)}")
        else:
            st.warning("Please enter a question.")


with tabs[2]:
    st.subheader("📊 Tax Dashboard")
    
    # Statement upload section
    stmt = st.file_uploader("Upload statement (PDF/CSV/OFX)", type=["pdf","csv","ofx"], key="stmt")
    if stmt:
        try:
            with st.spinner("Processing statement..."):
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(stmt.getbuffer())
                    tmp_path = tmp.name

                df = ingest_statement(tmp_path)
                os.unlink(tmp_path)

                mapping = {
                    "BizA": ["office_supplies", "meals_travel"],
                    "BizB": ["auto_expense"],
                    "BizC": ["software"],
                    "BizD": ["unclassified"],
                }
                df = tag_business(df, mapping)
                df.to_sql("transactions", conn, if_exists="append", index=False)
                st.success(f"✅ {len(df)} transactions processed from '{stmt.name}'")
                logger.info(f"Statement processed: {stmt.name}, {len(df)} transactions")
        except Exception as e:
            st.error(f"❌ Error processing statement: {str(e)}")
            logger.error(f"Statement processing error: {str(e)}")

    # Transaction display and analysis
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
    if cursor.fetchone():
        df = pd.read_sql("SELECT * FROM transactions ORDER BY date DESC", conn)
        
        if not df.empty:
            st.subheader("💰 Transaction Overview")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_transactions = len(df)
                st.metric("Total Transactions", total_transactions)
            with col2:
                total_spending = abs(df[df['amount'].astype(float) < 0]['amount'].astype(float).sum())
                st.metric("Total Spending", f"${total_spending:,.2f}")
            with col3:
                total_income = df[df['amount'].astype(float) > 0]['amount'].astype(float).sum()
                st.metric("Total Income", f"${total_income:,.2f}")
            with col4:
                net_flow = total_income - total_spending
                st.metric("Net Flow", f"${net_flow:,.2f}")
            
            # Show transactions table
            st.subheader("📋 Recent Transactions")
            st.dataframe(df.head(20), use_container_width=True)
            
            # Tax optimization section
            st.subheader("🎯 Tax Optimization")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📈 Run Tax Optimizer"):
                    try:
                        sugg = optimize(df)
                        if not sugg.empty:
                            st.subheader("💡 Tax Optimization Suggestions")
                            st.dataframe(sugg, use_container_width=True)
                        else:
                            st.info("No specific tax optimization suggestions at this time.")
                    except Exception as e:
                        st.error(f"❌ Error running optimizer: {str(e)}")
                        logger.error(f"Tax optimizer error: {str(e)}")
            
            with col2:
                if st.button("📊 Get Tax Insights"):
                    try:
                        insights = financial_analytics.get_tax_optimization_insights()
                        if "error" not in insights:
                            st.json(insights)
                        else:
                            st.error(insights["error"])
                    except Exception as e:
                        st.error(f"❌ Error getting insights: {str(e)}")
                        logger.error(f"Tax insights error: {str(e)}")
        else:
            st.info("No transaction data available. Upload a statement to get started.")
    else:
        st.info("No transaction data available. Upload a statement to get started.")

with tabs[3]:
    st.subheader("📈 Investment Dashboard")
    
    # Portfolio management
    st.subheader("💼 Portfolio Management")
    
    # Stock quotes section
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Stock Quotes")
        symbol = st.text_input("Enter stock symbol", "AAPL", key="stock_symbol")
        if st.button("Get Quote"):
            try:
                quote = stock_api.get_stock_quote(symbol)
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Price", f"${quote['price']:.2f}")
                with col_b:
                    st.metric("Change", f"${quote['change']:.2f}", delta=quote['change'])
                with col_c:
                    st.metric("Change %", quote['change_percent'])
                
                st.info(f"Volume: {quote['volume']:,}")
                
            except Exception as e:
                st.error(f"❌ Error fetching quote: {str(e)}")
                logger.error(f"Stock quote error: {str(e)}")
    
    with col2:
        st.subheader("🎯 Investment Recommendations")
        if 'user_profile' in st.session_state and st.session_state.user_profile:
            risk_tolerance = st.session_state.user_profile.get('risk_tolerance', 'moderate')
        else:
            risk_tolerance = st.selectbox("Risk Tolerance", ["conservative", "moderate", "aggressive"])
        
        if st.button("Get Recommendations"):
            try:
                recommendations = stock_api.get_investment_recommendations(risk_tolerance)
                st.subheader(f"💡 Recommendations for {risk_tolerance.title()} Risk")
                
                for rec in recommendations:
                    with st.expander(f"{rec['symbol']} - {rec['type']} ({rec['allocation']}%)"):
                        st.write(f"**Reason:** {rec['reason']}")
                        st.write(f"**Suggested Allocation:** {rec['allocation']}%")
                        
            except Exception as e:
                st.error(f"❌ Error getting recommendations: {str(e)}")
                logger.error(f"Investment recommendations error: {str(e)}")
    
    # Portfolio analysis section
    st.subheader("📊 Portfolio Analysis")
    
    # Simple portfolio input
    with st.expander("📝 Enter Your Holdings"):
        st.write("Enter your current stock holdings for analysis:")
        
        # Create a simple form for portfolio input
        holdings_data = []
        
        # Add some sample holdings for demo
        sample_holdings = [
            {"symbol": "AAPL", "shares": 10, "avg_cost": 150.00},
            {"symbol": "GOOGL", "shares": 5, "avg_cost": 2500.00},
            {"symbol": "MSFT", "shares": 15, "avg_cost": 280.00}
        ]
        
        if st.button("📊 Analyze Sample Portfolio"):
            try:
                analysis = stock_api.get_portfolio_analysis(sample_holdings)
                
                # Display overall portfolio metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Value", f"${analysis['total_value']:,.2f}")
                with col2:
                    st.metric("Total Cost", f"${analysis['total_cost']:,.2f}")
                with col3:
                    st.metric("Total Gain/Loss", f"${analysis['overall_gain_loss']:,.2f}")
                with col4:
                    st.metric("Gain/Loss %", f"{analysis['overall_gain_loss_percent']:.2f}%")
                
                # Display individual positions
                st.subheader("📈 Individual Positions")
                positions_df = pd.DataFrame(analysis['positions'])
                st.dataframe(positions_df, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Error analyzing portfolio: {str(e)}")
                logger.error(f"Portfolio analysis error: {str(e)}")

with tabs[4]:
    st.subheader("📊 Financial Analytics")
    
    # Analytics dashboard
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Spending Analysis")
        days = st.slider("Analysis Period (days)", 7, 365, 30)
        
        if st.button("📈 Analyze Spending"):
            try:
                analysis = financial_analytics.get_spending_analysis(days)
                
                if "error" not in analysis:
                    # Display metrics
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Total Spending", f"${analysis['total_spending']:,.2f}")
                        st.metric("Avg Daily Spending", f"${analysis['avg_daily_spending']:,.2f}")
                    with col_b:
                        st.metric("Total Income", f"${analysis['total_income']:,.2f}")
                        st.metric("Net Cash Flow", f"${analysis['net_cash_flow']:,.2f}")
                    
                    # Category breakdown
                    if analysis['category_breakdown']:
                        st.subheader("📊 Spending by Category")
                        category_df = pd.DataFrame(list(analysis['category_breakdown'].items()), 
                                                 columns=['Category', 'Amount'])
                        st.bar_chart(category_df.set_index('Category'))
                    
                    # Business breakdown
                    if analysis['business_breakdown']:
                        st.subheader("🏢 Spending by Business")
                        business_df = pd.DataFrame(list(analysis['business_breakdown'].items()), 
                                                 columns=['Business', 'Amount'])
                        st.bar_chart(business_df.set_index('Business'))
                else:
                    st.error(analysis['error'])
                    
            except Exception as e:
                st.error(f"❌ Error analyzing spending: {str(e)}")
                logger.error(f"Spending analysis error: {str(e)}")
    
    with col2:
        st.subheader("📋 Budget Recommendations")
        target_savings = st.slider("Target Savings Rate", 0.1, 0.5, 0.2, 0.05)
        
        if st.button("💡 Get Budget Advice"):
            try:
                budget_rec = financial_analytics.get_budget_recommendations(target_savings)
                
                if "error" not in budget_rec:
                    # Display savings metrics
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Current Savings Rate", f"{budget_rec['current_savings_rate']*100:.1f}%")
                        st.metric("Target Savings Rate", f"{budget_rec['target_savings_rate']*100:.1f}%")
                    with col_b:
                        st.metric("Current Savings", f"${budget_rec['current_savings_amount']:,.2f}")
                        st.metric("Savings Gap", f"${budget_rec['savings_gap']:,.2f}")
                    
                    # Recommendations
                    st.subheader("💡 Recommendations")
                    for rec in budget_rec['recommendations']:
                        st.write(f"• {rec}")
                else:
                    st.error(budget_rec['error'])
                    
            except Exception as e:
                st.error(f"❌ Error getting budget recommendations: {str(e)}")
                logger.error(f"Budget recommendations error: {str(e)}")
    
    # Comprehensive financial summary
    st.subheader("📊 Financial Summary")
    if st.button("📈 Generate Complete Financial Report"):
        try:
            with st.spinner("Generating comprehensive report..."):
                summary = financial_analytics.generate_financial_summary()
                
                st.subheader("📊 Complete Financial Analysis")
                
                # Display in tabs for better organization
                summary_tabs = st.tabs(["💰 Spending", "🏛️ Tax", "📋 Budget"])
                
                with summary_tabs[0]:
                    if "error" not in summary['spending_analysis']:
                        st.json(summary['spending_analysis'])
                    else:
                        st.error(summary['spending_analysis']['error'])
                
                with summary_tabs[1]:
                    if "error" not in summary['tax_insights']:
                        st.json(summary['tax_insights'])
                    else:
                        st.error(summary['tax_insights']['error'])
                
                with summary_tabs[2]:
                    if "error" not in summary['budget_recommendations']:
                        st.json(summary['budget_recommendations'])
                    else:
                        st.error(summary['budget_recommendations']['error'])
                        
        except Exception as e:
            st.error(f"❌ Error generating report: {str(e)}")
            logger.error(f"Financial summary error: {str(e)}")



# Footer
st.markdown("---")
st.markdown("🚀 **Financial Advisor Suite** - Your comprehensive financial management platform")
st.markdown("💡 Upload documents, analyze spending, optimize taxes, and get investment advice all in one place!")
st.markdown("📚 Documents are automatically loaded from `/docs` folder and processed daily at 2:00 AM")

