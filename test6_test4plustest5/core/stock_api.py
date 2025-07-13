import requests
import json
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import os

class StockAPI:
    """Stock market data and investment advice"""
    
    def __init__(self):
        self.alpha_vantage_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co/query"
        
    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time stock quote"""
        if not self.alpha_vantage_key:
            return self._get_mock_quote(symbol)
        
        try:
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key
            }
            
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if "Global Quote" in data:
                quote = data["Global Quote"]
                return {
                    "symbol": quote.get("01. symbol", symbol),
                    "price": float(quote.get("05. price", 0)),
                    "change": float(quote.get("09. change", 0)),
                    "change_percent": quote.get("10. change percent", "0%"),
                    "volume": int(quote.get("06. volume", 0)),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return self._get_mock_quote(symbol)
                
        except Exception as e:
            return self._get_mock_quote(symbol)
    
    def _get_mock_quote(self, symbol: str) -> Dict[str, Any]:
        """Mock data for development/demo"""
        mock_data = {
            "AAPL": {"price": 175.50, "change": 2.30, "change_percent": "1.33%"},
            "GOOGL": {"price": 2750.80, "change": -15.20, "change_percent": "-0.55%"},
            "MSFT": {"price": 310.20, "change": 5.80, "change_percent": "1.90%"},
            "TSLA": {"price": 185.30, "change": -3.70, "change_percent": "-1.96%"},
            "AMZN": {"price": 3380.50, "change": 45.20, "change_percent": "1.36%"},
            "NVDA": {"price": 485.60, "change": 12.40, "change_percent": "2.62%"},
            "SPY": {"price": 445.20, "change": 1.80, "change_percent": "0.41%"},
            "QQQ": {"price": 375.90, "change": 3.20, "change_percent": "0.86%"}
        }
        
        if symbol.upper() in mock_data:
            data = mock_data[symbol.upper()]
            return {
                "symbol": symbol.upper(),
                "price": data["price"],
                "change": data["change"],
                "change_percent": data["change_percent"],
                "volume": 1000000,
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "symbol": symbol.upper(),
            "price": 100.0,
            "change": 0.0,
            "change_percent": "0.00%",
            "volume": 0,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_portfolio_analysis(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze portfolio performance"""
        total_value = 0
        total_cost = 0
        positions = []
        
        for holding in holdings:
            symbol = holding.get("symbol", "")
            shares = holding.get("shares", 0)
            avg_cost = holding.get("avg_cost", 0)
            
            quote = self.get_stock_quote(symbol)
            current_price = quote["price"]
            current_value = shares * current_price
            cost_basis = shares * avg_cost
            
            gain_loss = current_value - cost_basis
            gain_loss_percent = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0
            
            positions.append({
                "symbol": symbol,
                "shares": shares,
                "avg_cost": avg_cost,
                "current_price": current_price,
                "current_value": current_value,
                "cost_basis": cost_basis,
                "gain_loss": gain_loss,
                "gain_loss_percent": gain_loss_percent
            })
            
            total_value += current_value
            total_cost += cost_basis
        
        overall_gain_loss = total_value - total_cost
        overall_gain_loss_percent = (overall_gain_loss / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "total_value": total_value,
            "total_cost": total_cost,
            "overall_gain_loss": overall_gain_loss,
            "overall_gain_loss_percent": overall_gain_loss_percent,
            "positions": positions,
            "analysis_date": datetime.now().isoformat()
        }
    
    def get_investment_recommendations(self, risk_tolerance: str = "moderate") -> List[Dict[str, Any]]:
        """Get investment recommendations based on risk tolerance"""
        recommendations = {
            "conservative": [
                {"symbol": "SPY", "type": "ETF", "reason": "Low-cost S&P 500 index fund", "allocation": 40},
                {"symbol": "BND", "type": "Bond ETF", "reason": "Broad bond market exposure", "allocation": 30},
                {"symbol": "VTI", "type": "Stock ETF", "reason": "Total stock market diversification", "allocation": 20},
                {"symbol": "Cash", "type": "Cash", "reason": "Emergency fund and stability", "allocation": 10}
            ],
            "moderate": [
                {"symbol": "VTI", "type": "Stock ETF", "reason": "Total stock market exposure", "allocation": 50},
                {"symbol": "VXUS", "type": "International ETF", "reason": "International diversification", "allocation": 20},
                {"symbol": "BND", "type": "Bond ETF", "reason": "Fixed income stability", "allocation": 20},
                {"symbol": "VNQ", "type": "REIT ETF", "reason": "Real estate exposure", "allocation": 10}
            ],
            "aggressive": [
                {"symbol": "QQQ", "type": "Tech ETF", "reason": "Technology sector growth", "allocation": 30},
                {"symbol": "VTI", "type": "Stock ETF", "reason": "Broad market exposure", "allocation": 25},
                {"symbol": "VXUS", "type": "International ETF", "reason": "International growth", "allocation": 20},
                {"symbol": "VUG", "type": "Growth ETF", "reason": "Growth stock focus", "allocation": 15},
                {"symbol": "ARKK", "type": "Innovation ETF", "reason": "Disruptive innovation", "allocation": 10}
            ]
        }
        
        return recommendations.get(risk_tolerance.lower(), recommendations["moderate"])

# Global instance
stock_api = StockAPI()