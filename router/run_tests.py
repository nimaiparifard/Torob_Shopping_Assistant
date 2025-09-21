#!/usr/bin/env python3
"""
Test runner for router system
Runs comprehensive tests, unit tests, or specific test categories
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from router.config import validate_config, print_config_summary


async def run_comprehensive_tests():
    """Run comprehensive integration tests"""
    print("🚀 اجرای تست‌های جامع...")
    
    try:
        from router.test_comprehensive import RouterTestSuite
        test_suite = RouterTestSuite()
        await test_suite.run_all_tests()
        return True
    except ImportError as e:
        print(f"❌ خطا در import: {e}")
        return False
    except Exception as e:
        print(f"❌ خطا در اجرای تست‌های جامع: {e}")
        return False


def run_unit_tests():
    """Run unit tests"""
    print("🧪 اجرای Unit Tests...")
    
    try:
        from router.test_units import run_all_unit_tests
        return run_all_unit_tests()
    except ImportError as e:
        print(f"❌ خطا در import: {e}")
        return False
    except Exception as e:
        print(f"❌ خطا در اجرای unit tests: {e}")
        return False


async def run_config_test():
    """Test configuration loading"""
    print("⚙️ تست پیکربندی...")
    
    try:
        from router.test_config import test_router_config
        await test_router_config()
        return True
    except ImportError as e:
        print(f"❌ خطا در import: {e}")
        return False
    except Exception as e:
        print(f"❌ خطا در تست پیکربندی: {e}")
        return False


async def run_quick_test():
    """Run quick functionality test"""
    print("⚡ تست سریع عملکرد...")
    
    try:
        from router import get_router_config_from_env, MainRouter, RouterState
        
        # Load config
        config = get_router_config_from_env()
        print("✅ پیکربندی بارگذاری شد")
        
        # Initialize router
        router = MainRouter(config)
        await router.initialize()
        print("✅ Router آماده شد")
        
        # Test simple query
        state = RouterState(user_query="سلام چطورید؟")
        decision = await router.route(state)
        
        print(f"✅ تست مسیریابی: {decision.agent.name} (اطمینان: {decision.confidence:.2f})")
        
        return True
    except Exception as e:
        print(f"❌ خطا در تست سریع: {e}")
        return False


async def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Router Test Runner")
    parser.add_argument(
        "--type", 
        choices=["all", "comprehensive", "unit", "config", "quick"],
        default="quick",
        help="نوع تست برای اجرا"
    )
    parser.add_argument(
        "--skip-config-check",
        action="store_true",
        help="رد کردن بررسی پیکربندی"
    )
    
    args = parser.parse_args()
    
    print("🧪 Router Test Runner")
    print("=" * 50)
    
    # Check configuration unless skipped
    if not args.skip_config_check:
        print("🔧 بررسی پیکربندی...")
        if not validate_config():
            print("❌ پیکربندی نامعتبر! لطفا فایل .env را بررسی کنید.")
            return False
        
        print_config_summary()
        print()
    
    success = True
    
    if args.type == "all":
        print("🎯 اجرای همه تست‌ها...")
        
        # Run all test types
        test_results = []
        
        print("\n" + "="*30 + " CONFIG TESTS " + "="*30)
        test_results.append(await run_config_test())
        
        print("\n" + "="*30 + " UNIT TESTS " + "="*30)
        test_results.append(run_unit_tests())
        
        print("\n" + "="*30 + " COMPREHENSIVE TESTS " + "="*30)
        test_results.append(await run_comprehensive_tests())
        
        success = all(test_results)
        
        print(f"\n📊 نتایج کلی: {sum(test_results)}/{len(test_results)} دسته تست موفق")
        
    elif args.type == "comprehensive":
        success = await run_comprehensive_tests()
        
    elif args.type == "unit":
        success = run_unit_tests()
        
    elif args.type == "config":
        success = await run_config_test()
        
    elif args.type == "quick":
        success = await run_quick_test()
    
    if success:
        print("\n🎉 همه تست‌ها موفق بودند!")
    else:
        print("\n❌ برخی تست‌ها ناموفق بودند!")
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ تست‌ها متوقف شدند.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 خطای غیرمنتظره: {e}")
        sys.exit(1)
