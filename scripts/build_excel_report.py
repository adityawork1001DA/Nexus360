from __future__ import annotations

from src.reporting.excel_report import NexusExcelReport


def main() -> None:

    print("=" * 76)
    print("NEXUS 360 - ADVANCED EXCEL BUSINESS INTELLIGENCE")
    print("=" * 76)

    print("\n[1/3] Loading semantic analytics datasets...")

    report = NexusExcelReport()

    print("[OK] Reporting engine initialized.")

    print("\n[2/3] Building enterprise Excel workbook...")

    output = report.build()

    print("[OK] Workbook generated.")

    print("\n[3/3] Finalizing workbook...")

    print("[OK] Excel BI layer completed.")

    print("\n" + "=" * 76)
    print("NEXUS 360 EXCEL REPORT BUILD COMPLETED")
    print("-" * 76)
    print(f"Workbook : {output}")
    print("-" * 76)
    print("Sheets   : 13")
    print("=" * 76)


if __name__ == "__main__":
    main()