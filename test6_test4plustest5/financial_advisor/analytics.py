import pandas as pd
import numpy as np
import sqlite3
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json

class FinancialAnalytics:
    """Comprehensive financial analytics and insights"""
    
    def __init__(self, db_path: str = "/app/data/finance.db"):
        self.db_path = db_path
        
    def get_spending_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Analyze spending patterns over specified days"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            
            # Get transactions from last N days
            query = """
            SELECT * FROM transactions 
            WHERE date >= date('now', '-{} days')
            ORDER BY date DESC
            """.format(days)
            
            df = pd.read_sql(query, conn)
            conn.close()
            
            if df.empty:
                return {"error": "No transaction data available"}
            
            # Convert amount to numeric
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            
            # Separate income and expenses
            expenses = df[df['amount'] < 0].copy()
            income = df[df['amount'] > 0].copy()
            
            # Category analysis
            category_spending = expenses.groupby('bucket')['amount'].sum().abs()
            
            # Daily spending trend
            expenses['date'] = pd.to_datetime(expenses['date'])
            daily_spending = expenses.groupby(expenses['date'].dt.date)['amount'].sum().abs()
            
            # Business classification analysis
            business_spending = expenses.groupby('business')['amount'].sum().abs()
            
            analysis = {
                "total_spending": abs(expenses['amount'].sum()),
                "total_income": income['amount'].sum(),
                "net_cash_flow": income['amount'].sum() + expenses['amount'].sum(),
                "avg_daily_spending": abs(expenses['amount'].sum()) / days,
                "category_breakdown": category_spending.to_dict(),
                "business_breakdown": business_spending.to_dict(),
                "daily_trend": daily_spending.to_dict(),
                "transaction_count": len(df),
                "analysis_period": f"{days} days"
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def get_tax_optimization_insights(self) -> Dict[str, Any]:
        """Generate tax optimization insights"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            df = pd.read_sql("SELECT * FROM transactions", conn)
            conn.close()
            
            if df.empty:
                return {"error": "No transaction data available"}
            
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            expenses = df[df['amount'] < 0].copy()
            
            # Tax-deductible categories
            tax_deductible = {
                'office_supplies': 0.5,  # 50% deductible
                'meals_travel': 0.5,     # 50% for meals, 100% for travel
                'auto_expense': 0.56,    # Standard mileage rate portion
                'software': 1.0          # 100% deductible
            }
            
            deductions = {}
            total_potential_deduction = 0
            
            for category, rate in tax_deductible.items():
                category_expenses = expenses[expenses['bucket'] == category]['amount'].sum()
                if category_expenses < 0:
                    deduction = abs(category_expenses) * rate
                    deductions[category] = {
                        'total_spent': abs(category_expenses),
                        'deduction_rate': rate,
                        'potential_deduction': deduction
                    }
                    total_potential_deduction += deduction
            
            # Estimated tax savings (assuming 22% tax bracket)
            estimated_tax_savings = total_potential_deduction * 0.22
            
            insights = {
                "total_potential_deductions": total_potential_deduction,
                "estimated_tax_savings": estimated_tax_savings,
                "deduction_breakdown": deductions,
                "recommendations": self._get_tax_recommendations(deductions),
                "analysis_date": datetime.now().isoformat()
            }
            
            return insights
            
        except Exception as e:
            return {"error": f"Tax analysis failed: {str(e)}"}
    
    def _get_tax_recommendations(self, deductions: Dict[str, Any]) -> List[str]:
        """Generate tax optimization recommendations"""
        recommendations = []
        
        for category, data in deductions.items():
            if data['potential_deduction'] > 1000:
                if category == 'office_supplies':
                    recommendations.append("Consider consolidating office supply purchases for better tracking")
                elif category == 'meals_travel':
                    recommendations.append("Maintain detailed records for meal and travel expenses")
                elif category == 'auto_expense':
                    recommendations.append("Track business mileage for maximum auto deductions")
                elif category == 'software':
                    recommendations.append("Software expenses are fully deductible - good category")
        
        if not recommendations:
            recommendations.append("Consider increasing business-related expenses to maximize deductions")
        
        return recommendations
    
    def get_budget_recommendations(self, target_savings_rate: float = 0.2) -> Dict[str, Any]:
        """Generate budget recommendations based on spending analysis"""
        analysis = self.get_spending_analysis(90)  # 3 months of data
        
        if "error" in analysis:
            return analysis
        
        total_income = analysis['total_income']
        total_spending = analysis['total_spending']
        
        if total_income <= 0:
            return {"error": "No income data available for budget analysis"}
        
        target_savings = total_income * target_savings_rate
        current_savings = total_income - total_spending
        savings_gap = target_savings - current_savings
        
        recommendations = []
        
        if savings_gap > 0:
            # Need to reduce spending
            category_spending = analysis['category_breakdown']
            
            # Find categories with highest spending
            sorted_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)
            
            recommendations.append(f"Need to save additional ${savings_gap:.2f} per month")
            recommendations.append(f"Consider reducing spending in top categories:")
            
            for category, amount in sorted_categories[:3]:
                reduction = min(amount * 0.1, savings_gap * 0.3)  # 10% reduction or portion of gap
                recommendations.append(f"- {category}: reduce by ${reduction:.2f}")
        else:
            recommendations.append("Great job! You're meeting your savings target")
            recommendations.append(f"Current savings rate: {(current_savings/total_income)*100:.1f}%")
        
        return {
            "target_savings_rate": target_savings_rate,
            "current_savings_rate": current_savings / total_income if total_income > 0 else 0,
            "target_savings_amount": target_savings,
            "current_savings_amount": current_savings,
            "savings_gap": savings_gap,
            "recommendations": recommendations,
            "analysis_date": datetime.now().isoformat()
        }
    
    def generate_financial_summary(self) -> Dict[str, Any]:
        """Generate comprehensive financial summary"""
        spending_analysis = self.get_spending_analysis(30)
        tax_insights = self.get_tax_optimization_insights()
        budget_rec = self.get_budget_recommendations()
        
        summary = {
            "spending_analysis": spending_analysis,
            "tax_insights": tax_insights,
            "budget_recommendations": budget_rec,
            "generated_at": datetime.now().isoformat()
        }
        
        return summary

# Global instance
financial_analytics = FinancialAnalytics()
