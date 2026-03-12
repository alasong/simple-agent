"""
Financial Tools Tests

Tests for financial domain extensions:
- Financial data handling
- Portfolio management
- Risk analysis
- Trading analysis
"""

import pytest
import sys
import importlib.util
from pathlib import Path

# Add project root to path
project_root = "/home/song/simple-agent"
sys.path.insert(0, project_root)

# Manually load the finance module
spec = importlib.util.spec_from_file_location(
    "finance",
    "/home/song/simple_agent/tools/finance/__init__.py"
)
finance_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finance_module)

# Import from manually loaded module
FinancialData = finance_module.FinancialData
PortfolioManager = finance_module.PortfolioManager
RiskAnalyzer = finance_module.RiskAnalyzer
TradingAnalyzer = finance_module.TradingAnalyzer
Portfolio = finance_module.Portfolio
RiskMetrics = finance_module.RiskMetrics
TradeSignal = finance_module.TradeSignal

# Also import ExtensionConfig from simple_agent.extensions
sys.path.insert(0, "/home/song/simple-agent")
from simple_agent.extensions import ExtensionConfig


class TestFinancialData:
    """Tests for FinancialData extension."""

    def test_creation(self):
        """Test financial data creation."""
        config = ExtensionConfig(name="financial_data_test")
        data = FinancialData(config)

        assert data.name == "financial_data"
        assert data.data_source == "mock"

    def test_fetch_prices(self):
        """Test price fetching."""
        data = FinancialData()
        prices = data.fetch_prices(["AAPL", "GOOGL", "MSFT"])

        assert "AAPL" in prices
        assert "GOOGL" in prices
        assert "MSFT" in prices
        assert prices["AAPL"] > 0
        assert prices["GOOGL"] > 0
        assert prices["MSFT"] > 0

    def test_fetch_prices_mock(self):
        """Test mock price fetching."""
        data = FinancialData()
        prices = data.fetch_prices(["AAPL", "NONEXISTENT"])

        assert prices["AAPL"] == 150.00
        assert prices["NONEXISTENT"] == 100.00

    def test_fetch_history(self):
        """Test price history fetching."""
        data = FinancialData()
        history = data.fetch_history("AAPL", days=30)

        assert len(history) == 30
        assert "date" in history[0]
        assert "open" in history[0]
        assert "high" in history[0]
        assert "low" in history[0]
        assert "close" in history[0]

    def test_load_unload(self):
        """Test load and unload."""
        data = FinancialData()
        data.load()

        assert "loaded_at" in data._metadata
        assert data._metadata["version"] == "1.0.0"

        data.unload()


class TestPortfolioManager:
    """Tests for PortfolioManager extension."""

    def test_creation(self):
        """Test portfolio manager creation."""
        config = ExtensionConfig(name="portfolio_manager_test")
        manager = PortfolioManager(config)

        assert manager.name == "portfolio_manager"
        assert len(manager.portfolios) == 0

    def test_create_portfolio(self):
        """Test portfolio creation."""
        manager = PortfolioManager()
        portfolio = manager.create_portfolio("test_portfolio", initial_cash=10000.0)

        assert portfolio.name == "test_portfolio"
        assert portfolio.cash == 10000.0
        assert len(portfolio.assets) == 0
        assert portfolio.total_value == 10000.0

    def test_add_asset(self):
        """Test adding assets to portfolio."""
        manager = PortfolioManager()
        manager.create_portfolio("test", 10000.0)

        result = manager.add_asset("test", "AAPL", 10)

        assert result is True
        assert manager.portfolios["test"].assets["AAPL"] == 10.0

    def test_remove_asset(self):
        """Test removing assets from portfolio."""
        manager = PortfolioManager()
        manager.create_portfolio("test", 10000.0)
        manager.add_asset("test", "AAPL", 10)

        result = manager.remove_asset("test", "AAPL")

        assert result is True
        assert "AAPL" not in manager.portfolios["test"].assets

    def test_update_cash(self):
        """Test updating cash balance."""
        manager = PortfolioManager()
        manager.create_portfolio("test", 10000.0)

        result = manager.update_cash("test", 500.0)

        assert result is True
        assert manager.portfolios["test"].cash == 10500.0

    def test_get_all_portfolios(self):
        """Test getting all portfolios."""
        manager = PortfolioManager()
        manager.create_portfolio("portfolio1", 1000.0)
        manager.create_portfolio("portfolio2", 2000.0)

        all_pfs = manager.get_all_portfolios()

        assert len(all_pfs) == 2
        assert "portfolio1" in all_pfs
        assert "portfolio2" in all_pfs

    def test_load_unload(self):
        """Test load and unload."""
        manager = PortfolioManager()
        manager.load()

        assert "loaded_at" in manager._metadata
        assert manager._metadata["version"] == "1.0.0"

        manager.unload()
        assert len(manager.portfolios) == 0


class TestRiskAnalyzer:
    """Tests for RiskAnalyzer extension."""

    def test_creation(self):
        """Test risk analyzer creation."""
        config = ExtensionConfig(name="risk_analyzer_test")
        analyzer = RiskAnalyzer(config)

        assert analyzer.name == "risk_analyzer"
        assert analyzer.risk_limits["max_var_95"] == 0.05

    def test_calculate_var(self):
        """Test VaR calculation."""
        analyzer = RiskAnalyzer()
        returns = [-0.02, -0.01, 0.01, 0.02, -0.03, 0.015, -0.01, 0.005]

        var_95 = analyzer.calculate_var(returns, 0.95)

        assert var_95 >= 0
        assert var_95 <= 1

    def test_calculate_var_empty(self):
        """Test VaR with empty returns."""
        analyzer = RiskAnalyzer()
        var = analyzer.calculate_var([], 0.95)

        assert var == 0.0

    def test_calculate_volatility(self):
        """Test volatility calculation."""
        analyzer = RiskAnalyzer()
        returns = [0.01, -0.01, 0.02, -0.02, 0.015, -0.015]

        vol = analyzer.calculate_volatility(returns)

        assert vol >= 0
        assert vol <= 1

    def test_calculate_sharpe(self):
        """Test Sharpe ratio calculation."""
        analyzer = RiskAnalyzer()
        returns = [0.01, 0.02, 0.015, 0.025, 0.018]

        sharpe = analyzer.calculate_sharpe(returns)

        assert isinstance(sharpe, float)

    def test_calculate_max_drawdown(self):
        """Test max drawdown calculation."""
        analyzer = RiskAnalyzer()
        cumulative = [1.0, 1.05, 1.10, 1.08, 1.15, 1.12, 1.20, 1.18]

        max_dd = analyzer.calculate_max_drawdown(cumulative)

        assert max_dd >= 0
        assert max_dd < 0.2  # Should be small for this data

    def test_analyze_portfolio(self):
        """Test portfolio analysis."""
        analyzer = RiskAnalyzer()
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.01]
        portfolio = Portfolio(name="test", assets={"AAPL": 100}, cash=1000)

        metrics = analyzer.analyze_portfolio(portfolio, returns)

        assert isinstance(metrics, RiskMetrics)
        assert metrics.var_95 >= 0
        assert metrics.volatility >= 0

    def test_check_risk_limits(self):
        """Test risk limit checking."""
        analyzer = RiskAnalyzer()
        metrics = RiskMetrics(var_95=0.10, max_drawdown=0.25)

        violations = analyzer.check_risk_limits(metrics)

        assert len(violations) >= 1

    def test_load_unload(self):
        """Test load and unload."""
        analyzer = RiskAnalyzer()
        analyzer.load()

        assert "loaded_at" in analyzer._metadata
        assert analyzer._metadata["version"] == "1.0.0"

        analyzer.unload()
        assert len(analyzer.risk_limits) == 0


class TestTradingAnalyzer:
    """Tests for TradingAnalyzer extension."""

    def test_creation(self):
        """Test trading analyzer creation."""
        config = ExtensionConfig(name="trading_analyzer_test")
        analyzer = TradingAnalyzer(config)

        assert analyzer.name == "trading_analyzer"

    def test_moving_average(self):
        """Test moving average calculation."""
        analyzer = TradingAnalyzer()
        prices = [100, 102, 101, 103, 104, 102, 105, 106, 104, 107]

        ma = analyzer.moving_average(prices, window=3)

        assert len(ma) == len(prices) - 3 + 1
        assert ma[0] == 101.0  # (100+102+101)/3
        assert ma[1] == 102.0  # (102+101+103)/3

    def test_moving_average_short(self):
        """Test moving average with short data."""
        analyzer = TradingAnalyzer()
        prices = [100, 102]

        ma = analyzer.moving_average(prices, window=5)

        assert len(ma) == 1
        assert ma[0] == 101.0

    def test_relative_strength(self):
        """Test RSI-like calculation."""
        analyzer = TradingAnalyzer()
        prices = [100, 102, 101, 103, 104, 105, 104, 106, 107, 108, 107, 109, 110]

        rsi = analyzer.relative_strength(prices, period=5)

        assert len(rsi) == len(prices) - 5
        assert all(0 <= r <= 100 for r in rsi)

    def test_generate_signal_buy(self):
        """Test buy signal generation."""
        analyzer = TradingAnalyzer()
        prices = [100] * 20  # Flat prices, current slightly below average
        prices[-1] = 95

        signal = analyzer.generate_signal("AAPL", prices, strategy="簡單")

        assert signal.symbol == "AAPL"
        assert signal.action == "buy"

    def test_generate_signal_sell(self):
        """Test sell signal generation."""
        analyzer = TradingAnalyzer()
        prices = [100] * 20  # Flat prices, current slightly above average
        prices[-1] = 105

        signal = analyzer.generate_signal("AAPL", prices, strategy="簡單")

        assert signal.symbol == "AAPL"
        assert signal.action == "sell"

    def test_generate_signal_hold(self):
        """Test hold signal generation."""
        analyzer = TradingAnalyzer()
        prices = [100] * 5  # Very few prices

        signal = analyzer.generate_signal("AAPL", prices, strategy="簡單")

        assert signal.symbol == "AAPL"
        assert signal.action == "hold"

    def test_backtest_strategy(self):
        """Test strategy backtesting."""
        analyzer = TradingAnalyzer()
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 110]

        result = analyzer.backtest_strategy(prices, strategy="簡單")

        assert "initial_price" in result
        assert "final_price" in result
        assert "total_return" in result
        assert "max_drawdown" in result
        assert result["initial_price"] == 100
        assert result["final_price"] == 110
        assert result["total_return"] == 0.10

    def test_load_unload(self):
        """Test load and unload."""
        analyzer = TradingAnalyzer()
        analyzer.load()

        assert "loaded_at" in analyzer._metadata
        assert analyzer._metadata["version"] == "1.0.0"

        analyzer.unload()
        assert len(analyzer.strategies) == 0


class TestIntegration:
    """Integration tests for financial tools."""

    def test_full_workflow(self):
        """Test complete financial workflow."""
        portfolio_manager = PortfolioManager()
        risk_analyzer = RiskAnalyzer()

        # Create portfolio
        portfolio = portfolio_manager.create_portfolio("investment", 10000.0)

        # Add some assets
        portfolio_manager.add_asset("investment", "AAPL", 10)
        portfolio_manager.add_asset("investment", "GOOGL", 5)

        # Check portfolio
        assert portfolio.total_value > 0

        # Analyze risk
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        metrics = risk_analyzer.analyze_portfolio(portfolio, returns)

        assert metrics.var_95 >= 0
        assert metrics.volatility >= 0

    def test_trading_signals_and_analysis(self):
        """Test trading signal generation and analysis."""
        trading_analyzer = TradingAnalyzer()

        # Generate signals
        prices = [100, 101, 102, 103, 102, 104, 105, 104, 106, 107, 108]

        signal = trading_analyzer.generate_signal("TEST", prices, strategy="趨勢追蹤")

        assert signal.symbol == "TEST"
        assert signal.action in ["buy", "sell", "hold"]
        assert 0 <= signal.strength <= 1
        assert 0 <= signal.confidence <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
