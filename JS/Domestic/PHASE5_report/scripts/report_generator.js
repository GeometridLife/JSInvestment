/**
 * PHASE5 Report - Step 3: docx 리포트 생성기
 * Date: 2026-05-01
 *
 * Description:
 *   - Step 2의 분석 결과 JSON을 읽어 마이크로인피니티 예시 형식의 .docx 생성
 *   - 출력: result/{tier1섹터}/{year}/{quarter}/{회사명}_분석보고서.docx
 *
 * Usage:
 *   node scripts/report_generator.js --input cache/005930_2025_4Q_analysis.json
 *   node scripts/report_generator.js --year 2025 --quarter 4Q
 *   node scripts/report_generator.js --year 2025 --quarter 4Q --sector 반도체
 */

const fs = require("fs");
const path = require("path");
const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  Table,
  TableRow,
  TableCell,
  Header,
  Footer,
  AlignmentType,
  HeadingLevel,
  BorderStyle,
  WidthType,
  ShadingType,
  PageNumber,
  PageBreak,
  LevelFormat,
} = require("docx");

// ============================================================
// 설정
// ============================================================
const SCRIPT_DIR = __dirname;
const BASE_DIR = path.dirname(SCRIPT_DIR);
const DOMESTIC_DIR = path.dirname(BASE_DIR);
const PHASE0_DIR = path.join(DOMESTIC_DIR, "PHASE0_classification");
const CACHE_DIR = path.join(BASE_DIR, "cache");
const RESULT_DIR = path.join(BASE_DIR, "result");

// 컬러 코드 표준
const COLORS = {
  HEADER: "1F4E78", // 남색
  SUB_HEADER: "2E75B6", // 밝은 파랑
  BULL: "00B050", // 초록
  BULL_BG: "E2EFDA",
  WATCH: "ED7D31", // 주황
  WATCH_BG: "FFF2CC",
  RISK: "C00000", // 빨강
  RISK_BG: "FCE4D6",
  TABLE_HEADER_BG: "D5E8F0",
  EXEC_SUMMARY_BG: "DEEBF7",
  BODY: "333333",
  GRAY: "595959",
  LIGHT_GRAY: "808080",
};

// 테이블 공통 스타일
const BORDER = {
  style: BorderStyle.SINGLE,
  size: 1,
  color: "CCCCCC",
};
const BORDERS = {
  top: BORDER,
  bottom: BORDER,
  left: BORDER,
  right: BORDER,
};
const CELL_MARGINS = {
  top: 80,
  bottom: 80,
  left: 120,
  right: 120,
};
const TABLE_WIDTH = 9360; // US Letter, 1" margins

// ============================================================
// 유틸리티
// ============================================================

/** 안전하게 문자열 변환 */
function str(val) {
  if (val === null || val === undefined) return "";
  return String(val);
}

/** 텍스트를 여러 줄로 분리해 Paragraph 배열 반환 */
function textToParagraphs(text, options = {}) {
  if (!text) return [new Paragraph({ children: [] })];
  const lines = str(text).split("\n");
  return lines.map(
    (line) =>
      new Paragraph({
        spacing: { after: 100, line: 300 },
        ...options,
        children: [
          new TextRun({
            text: line,
            font: "Malgun Gothic",
            size: 22,
            color: COLORS.BODY,
            ...(options.run || {}),
          }),
        ],
      })
  );
}

/** 헤더 제목 Paragraph */
function sectionHeading(text, level = HeadingLevel.HEADING_1) {
  return new Paragraph({
    heading: level,
    spacing: { before: 360, after: 200, line: 320 },
    border: {
      bottom: {
        style: BorderStyle.SINGLE,
        size: 12,
        color: COLORS.HEADER,
        space: 4,
      },
    },
    children: [
      new TextRun({
        text: text,
        font: "Malgun Gothic",
        bold: true,
        color: COLORS.HEADER,
        size: level === HeadingLevel.HEADING_1 ? 32 : 28,
      }),
    ],
  });
}

/** 서브 헤더 */
function subHeading(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 140, line: 320 },
    children: [
      new TextRun({
        text: text,
        font: "Malgun Gothic",
        bold: true,
        color: COLORS.SUB_HEADER,
        size: 26,
      }),
    ],
  });
}

/** 시그널 박스 (Bull/Watch/Risk) */
function signalBox(label, items, type) {
  const colorMap = {
    bull: { text: COLORS.BULL, bg: COLORS.BULL_BG, icon: "▲" },
    watch: { text: COLORS.WATCH, bg: COLORS.WATCH_BG, icon: "●" },
    risk: { text: COLORS.RISK, bg: COLORS.RISK_BG, icon: "▼" },
  };
  const c = colorMap[type] || colorMap.watch;

  const cellChildren = [
    new Paragraph({
      spacing: { after: 80 },
      children: [
        new TextRun({
          text: `${c.icon} ${label}`,
          font: "Malgun Gothic",
          bold: true,
          color: c.text,
          size: 24,
        }),
      ],
    }),
  ];

  if (Array.isArray(items)) {
    items.forEach((item) => {
      cellChildren.push(
        new Paragraph({
          spacing: { after: 40 },
          indent: { left: 360 },
          children: [
            new TextRun({
              text: `- ${str(item)}`,
              font: "Malgun Gothic",
              size: 21,
              color: COLORS.BODY,
            }),
          ],
        })
      );
    });
  }

  return new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths: [TABLE_WIDTH],
    rows: [
      new TableRow({
        children: [
          new TableCell({
            width: { size: TABLE_WIDTH, type: WidthType.DXA },
            borders: {
              top: {
                style: BorderStyle.SINGLE,
                size: 8,
                color: c.text,
              },
              bottom: {
                style: BorderStyle.SINGLE,
                size: 1,
                color: "DDDDDD",
              },
              left: {
                style: BorderStyle.SINGLE,
                size: 1,
                color: "DDDDDD",
              },
              right: {
                style: BorderStyle.SINGLE,
                size: 1,
                color: "DDDDDD",
              },
            },
            shading: { fill: c.bg, type: ShadingType.CLEAR },
            margins: { top: 120, bottom: 120, left: 200, right: 200 },
            children: cellChildren,
          }),
        ],
      }),
    ],
  });
}

/** 데이터 테이블 생성 */
function dataTable(headers, rows, colWidths = null) {
  const numCols = headers.length;
  const defaultWidth = Math.floor(TABLE_WIDTH / numCols);
  const widths = colWidths || headers.map(() => defaultWidth);

  // 헤더 행
  const headerRow = new TableRow({
    children: headers.map((h, i) =>
      new TableCell({
        width: { size: widths[i], type: WidthType.DXA },
        borders: BORDERS,
        shading: {
          fill: COLORS.TABLE_HEADER_BG,
          type: ShadingType.CLEAR,
        },
        margins: CELL_MARGINS,
        children: [
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({
                text: str(h),
                font: "Malgun Gothic",
                bold: true,
                size: 20,
                color: COLORS.HEADER,
              }),
            ],
          }),
        ],
      })
    ),
  });

  // 데이터 행
  const dataRows = rows.map(
    (row) =>
      new TableRow({
        children: row.map((cell, i) =>
          new TableCell({
            width: { size: widths[i], type: WidthType.DXA },
            borders: BORDERS,
            margins: CELL_MARGINS,
            children: [
              new Paragraph({
                alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT,
                children: [
                  new TextRun({
                    text: str(cell),
                    font: "Malgun Gothic",
                    size: 20,
                    color: COLORS.BODY,
                  }),
                ],
              }),
            ],
          })
        ),
      })
  );

  return new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths: widths,
    rows: [headerRow, ...dataRows],
  });
}

// ============================================================
// 리포트 빌더
// ============================================================

function buildReport(analysis) {
  const report = analysis.final_report || analysis.step4_json || {};
  const name = analysis.name || "Unknown";
  const year = analysis.year || "";
  const quarter = analysis.quarter || "";

  // 메타 정보 (step1에서)
  const step1 = analysis.step1_json || {};
  const meta = step1.meta || {};

  const children = [];

  // --- 표지 ---
  children.push(
    new Paragraph({
      spacing: { before: 2000, after: 400 },
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({
          text: "Financial Audit Report Analysis",
          font: "Malgun Gothic",
          italics: true,
          color: COLORS.LIGHT_GRAY,
          size: 28,
        }),
      ],
    })
  );

  children.push(
    new Paragraph({
      spacing: { before: 200, after: 200 },
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({
          text: name,
          font: "Malgun Gothic",
          bold: true,
          color: COLORS.HEADER,
          size: 56,
        }),
      ],
    })
  );

  const periodLabel =
    quarter === "4Q"
      ? `제${year}기 사업보고서 심층 분석`
      : `${year}년 ${quarter} 분기보고서 심층 분석`;
  children.push(
    new Paragraph({
      spacing: { before: 100, after: 800 },
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({
          text: periodLabel,
          font: "Malgun Gothic",
          color: "404040",
          size: 36,
        }),
      ],
    })
  );

  // 감사인/의견/분석일
  const metaLines = [
    `보고기간: ${str(meta.fiscal_period || `${year}년`)}`,
    `감사인: ${str(meta.auditor || "확인 필요")} (${str(meta.audit_opinion || "확인 필요")})`,
    `분석일: ${new Date().toISOString().slice(0, 10).replace(/-/g, ".")}`,
  ];
  metaLines.forEach((line) => {
    children.push(
      new Paragraph({
        spacing: { before: 100, after: 100 },
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({
            text: line,
            font: "Malgun Gothic",
            color: COLORS.GRAY,
            size: 24,
          }),
        ],
      })
    );
  });

  // --- 핵심 결론 박스 ---
  children.push(new Paragraph({ spacing: { before: 400, after: 200 } }));
  children.push(
    new Paragraph({
      spacing: { before: 400, after: 200 },
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({
          text: "핵심 결론",
          font: "Malgun Gothic",
          bold: true,
          color: COLORS.RISK,
          size: 24,
        }),
      ],
    })
  );

  const execSummary = str(
    report.executive_summary || "분석 결과를 확인하세요."
  );
  children.push(
    new Table({
      width: { size: TABLE_WIDTH, type: WidthType.DXA },
      columnWidths: [TABLE_WIDTH],
      rows: [
        new TableRow({
          children: [
            new TableCell({
              width: { size: TABLE_WIDTH, type: WidthType.DXA },
              borders: {
                top: { style: BorderStyle.SINGLE, size: 12, color: COLORS.HEADER },
                left: { style: BorderStyle.SINGLE, size: 12, color: COLORS.HEADER },
                bottom: { style: BorderStyle.SINGLE, size: 12, color: COLORS.HEADER },
                right: { style: BorderStyle.SINGLE, size: 12, color: COLORS.HEADER },
              },
              shading: {
                fill: COLORS.EXEC_SUMMARY_BG,
                type: ShadingType.CLEAR,
              },
              margins: { top: 200, bottom: 200, left: 200, right: 200 },
              children: [
                new Paragraph({
                  spacing: { line: 360 },
                  alignment: AlignmentType.CENTER,
                  children: [
                    new TextRun({
                      text: execSummary,
                      font: "Malgun Gothic",
                      bold: true,
                      italics: true,
                      color: COLORS.HEADER,
                      size: 24,
                    }),
                  ],
                }),
              ],
            }),
          ],
        }),
      ],
    })
  );

  // 페이지 브레이크
  children.push(new Paragraph({ children: [new PageBreak()] }));

  // --- 1. 회사 개요 ---
  const s1 = report.section_1_company_overview || {};
  children.push(sectionHeading("1. 회사 개요"));

  if (s1.basic_info_table && s1.basic_info_table.length > 0) {
    const infoRows = s1.basic_info_table.map((r) => [
      str(r["항목"] || r.item || ""),
      str(r["내용"] || r.content || ""),
    ]);
    children.push(dataTable(["항목", "내용"], infoRows, [2800, 6560]));
  }

  if (s1.business_identity) {
    children.push(new Paragraph({ spacing: { before: 200 } }));
    children.push(subHeading("사업 정체성"));
    textToParagraphs(s1.business_identity).forEach((p) => children.push(p));
  }

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // --- 2. 손익 분석 ---
  const s2 = report.section_2_income_analysis || {};
  children.push(sectionHeading("2. 손익 분석"));

  if (s2.key_metrics_table && s2.key_metrics_table.length > 0) {
    const incomeRows = s2.key_metrics_table.map((r) => [
      str(r["지표"] || r.metric || ""),
      str(r["당기"] || r.current || ""),
      str(r["전기"] || r.previous || ""),
      str(r["증감률"] || r.change_rate || ""),
    ]);
    children.push(
      dataTable(["지표", "당기", "전기", "증감률"], incomeRows, [
        2500, 2300, 2300, 2260,
      ])
    );
  }

  if (s2.analysis_text) {
    children.push(new Paragraph({ spacing: { before: 200 } }));
    textToParagraphs(s2.analysis_text).forEach((p) => children.push(p));
  }

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // --- 3. 재무상태 분석 ---
  const s3 = report.section_3_balance_sheet || {};
  children.push(sectionHeading("3. 재무상태 분석"));

  if (s3.summary_table && s3.summary_table.length > 0) {
    const bsRows = s3.summary_table.map((r) => [
      str(r["항목"] || r.item || ""),
      str(r["당기"] || r.current || ""),
      str(r["전기"] || r.previous || ""),
      str(r["증감"] || r.change || ""),
    ]);
    children.push(
      dataTable(["항목", "당기", "전기", "증감"], bsRows, [
        2500, 2300, 2300, 2260,
      ])
    );
  }

  if (s3.key_ratios && s3.key_ratios.length > 0) {
    children.push(new Paragraph({ spacing: { before: 200 } }));
    children.push(subHeading("핵심 비율"));
    const ratioRows = s3.key_ratios.map((r) => [
      str(r["비율"] || r.ratio || ""),
      str(r["값"] || r.value || ""),
      str(r["평가"] || r.assessment || ""),
    ]);
    children.push(
      dataTable(["비율", "값", "평가"], ratioRows, [2500, 2300, 4560])
    );
  }

  if (s3.analysis_text) {
    children.push(new Paragraph({ spacing: { before: 200 } }));
    textToParagraphs(s3.analysis_text).forEach((p) => children.push(p));
  }

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // --- 4. 핵심 리스크 ---
  const s4 = report.section_4_key_risks || {};
  children.push(sectionHeading("4. 핵심 리스크"));

  if (s4.risks && s4.risks.length > 0) {
    s4.risks.forEach((risk, i) => {
      const severity = str(risk.severity || "medium").toLowerCase();
      children.push(
        new Paragraph({
          spacing: { before: 200, after: 100 },
          children: [
            new TextRun({
              text: `리스크 ${i + 1}: ${str(risk.title || "")}`,
              font: "Malgun Gothic",
              bold: true,
              color: severity === "high" ? COLORS.RISK : COLORS.WATCH,
              size: 24,
            }),
          ],
        })
      );
      textToParagraphs(risk.description).forEach((p) => children.push(p));
    });
  }

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // --- 5. 주주 구성 ---
  const s5 = report.section_5_shareholder || {};
  children.push(sectionHeading("5. 주주 구성"));

  if (s5.cap_table && s5.cap_table.length > 0) {
    const capRows = s5.cap_table.map((r) => [
      str(r["주주명"] || r.shareholder || ""),
      str(r["지분율"] || r.ratio || ""),
      str(r["비고"] || r.note || ""),
    ]);
    children.push(
      dataTable(["주주명", "지분율", "비고"], capRows, [3200, 2000, 4160])
    );
  }

  if (s5.ipo_stage) {
    children.push(new Paragraph({ spacing: { before: 200 } }));
    children.push(subHeading("IPO 단계 진단"));
    textToParagraphs(s5.ipo_stage).forEach((p) => children.push(p));
  }

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // --- 6. 현금흐름 분석 ---
  const s6 = report.section_6_cashflow || {};
  children.push(sectionHeading("6. 현금흐름 분석"));

  if (s6.summary_table && s6.summary_table.length > 0) {
    const cfRows = s6.summary_table.map((r) => [
      str(r["활동"] || r.activity || ""),
      str(r["금액"] || r.amount || ""),
      str(r["전기"] || r.previous || ""),
    ]);
    children.push(
      dataTable(["활동", "당기", "전기"], cfRows, [3200, 3080, 3080])
    );
  }

  if (s6.cash_conversion_ratio) {
    children.push(
      new Paragraph({
        spacing: { before: 200, after: 100 },
        children: [
          new TextRun({
            text: `현금전환비율: ${str(s6.cash_conversion_ratio)}`,
            font: "Malgun Gothic",
            bold: true,
            size: 22,
            color: COLORS.BODY,
          }),
        ],
      })
    );
  }

  if (s6.quality_of_earnings) {
    children.push(subHeading("이익의 질 진단"));
    textToParagraphs(s6.quality_of_earnings).forEach((p) => children.push(p));
  }

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // --- 7. 자금 부담 및 우발채무 ---
  const s7 = report.section_7_contingent || {};
  children.push(sectionHeading("7. 자금 부담 및 우발채무"));

  if (s7.guarantees && s7.guarantees.length > 0) {
    const guarRows = s7.guarantees.map((r) => [
      str(r["구분"] || r.type || ""),
      str(r["금액"] || r.amount || ""),
      str(r["비고"] || r.note || ""),
    ]);
    children.push(
      dataTable(["구분", "금액", "비고"], guarRows, [3200, 2500, 3660])
    );
  }

  if (s7.upcoming_events) {
    children.push(new Paragraph({ spacing: { before: 200 } }));
    children.push(subHeading("차기 자금 이벤트"));
    textToParagraphs(s7.upcoming_events).forEach((p) => children.push(p));
  }

  if (s7.analysis_text) {
    children.push(new Paragraph({ spacing: { before: 200 } }));
    textToParagraphs(s7.analysis_text).forEach((p) => children.push(p));
  }

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // --- 8. 추가 운영 신호 ---
  const s8 = report.section_8_operational_signals || {};
  children.push(sectionHeading("8. 추가 운영 신호"));

  if (s8.signals && s8.signals.length > 0) {
    const sigRows = s8.signals.map((r) => [
      str(r.category || ""),
      str(r.finding || ""),
      str(r.implication || ""),
    ]);
    children.push(
      dataTable(["분류", "발견 사항", "시사점"], sigRows, [2000, 3680, 3680])
    );
  }

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // --- 9. 종합 진단 ---
  const s9 = report.section_9_diagnosis || {};
  children.push(sectionHeading("9. 종합 진단"));

  if (s9.bull_case && s9.bull_case.length > 0) {
    children.push(signalBox("Bull Case", s9.bull_case, "bull"));
    children.push(new Paragraph({ spacing: { before: 200 } }));
  }

  if (s9.watch_list && s9.watch_list.length > 0) {
    children.push(signalBox("Watch List", s9.watch_list, "watch"));
    children.push(new Paragraph({ spacing: { before: 200 } }));
  }

  if (s9.risk_factors && s9.risk_factors.length > 0) {
    children.push(signalBox("Risk Factors", s9.risk_factors, "risk"));
    children.push(new Paragraph({ spacing: { before: 200 } }));
  }

  if (s9.one_liner) {
    children.push(subHeading("한 줄 요약"));
    children.push(
      new Paragraph({
        spacing: { after: 100 },
        children: [
          new TextRun({
            text: str(s9.one_liner),
            font: "Malgun Gothic",
            bold: true,
            size: 24,
            color: COLORS.HEADER,
          }),
        ],
      })
    );
  }

  if (s9.industry_context) {
    children.push(subHeading("산업 맥락"));
    textToParagraphs(s9.industry_context).forEach((p) => children.push(p));
  }

  children.push(new Paragraph({ children: [new PageBreak()] }));

  // --- 10. 분석 한계 ---
  const s10 = report.section_10_limitations || [];
  children.push(sectionHeading("10. 분석 한계 및 추가 검토 권장 항목"));

  if (Array.isArray(s10) && s10.length > 0) {
    s10.forEach((item) => {
      children.push(
        new Paragraph({
          spacing: { after: 80 },
          indent: { left: 360 },
          children: [
            new TextRun({
              text: `- ${str(item)}`,
              font: "Malgun Gothic",
              size: 21,
              color: COLORS.GRAY,
            }),
          ],
        })
      );
    });
  }

  // --- 면책 조항 ---
  children.push(new Paragraph({ spacing: { before: 600 } }));
  children.push(
    new Paragraph({
      spacing: { before: 200, after: 100 },
      border: {
        top: {
          style: BorderStyle.SINGLE,
          size: 6,
          color: "CCCCCC",
          space: 8,
        },
      },
      children: [
        new TextRun({
          text: "본 분석은 공시된 감사/사업보고서를 기반으로 AI가 자동 생성한 것으로, 투자 권유가 아닙니다. 정확성을 보장하지 않으며, 투자 의사결정 시 반드시 원본 보고서와 전문가 의견을 참조하시기 바랍니다.",
          font: "Malgun Gothic",
          size: 18,
          color: COLORS.LIGHT_GRAY,
          italics: true,
        }),
      ],
    })
  );

  // --- 문서 생성 ---
  const doc = new Document({
    styles: {
      default: {
        document: {
          run: { font: "Malgun Gothic", size: 22 },
        },
      },
      paragraphStyles: [
        {
          id: "Heading1",
          name: "Heading 1",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { size: 32, bold: true, font: "Malgun Gothic" },
          paragraph: {
            spacing: { before: 360, after: 200 },
            outlineLevel: 0,
          },
        },
        {
          id: "Heading2",
          name: "Heading 2",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { size: 26, bold: true, font: "Malgun Gothic" },
          paragraph: {
            spacing: { before: 280, after: 140 },
            outlineLevel: 1,
          },
        },
      ],
    },
    sections: [
      {
        properties: {
          page: {
            size: { width: 12240, height: 15840 },
            margin: {
              top: 1440,
              right: 1440,
              bottom: 1440,
              left: 1440,
            },
          },
        },
        headers: {
          default: new Header({
            children: [
              new Paragraph({
                alignment: AlignmentType.RIGHT,
                children: [
                  new TextRun({
                    text: `${name} | ${year} ${quarter} 분석보고서`,
                    font: "Malgun Gothic",
                    size: 16,
                    color: COLORS.LIGHT_GRAY,
                  }),
                ],
              }),
            ],
          }),
        },
        footers: {
          default: new Footer({
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [
                  new TextRun({
                    text: "Page ",
                    font: "Malgun Gothic",
                    size: 16,
                    color: COLORS.LIGHT_GRAY,
                  }),
                  new TextRun({
                    children: [PageNumber.CURRENT],
                    font: "Malgun Gothic",
                    size: 16,
                    color: COLORS.LIGHT_GRAY,
                  }),
                ],
              }),
            ],
          }),
        },
        children: children,
      },
    ],
  });

  return doc;
}

// ============================================================
// 섹터 매핑 로드
// ============================================================
function loadSectorMap() {
  const csvPath = path.join(
    PHASE0_DIR,
    "kospi_kosdaq_sector_classification.csv"
  );
  if (!fs.existsSync(csvPath)) return {};

  const content = fs.readFileSync(csvPath, "utf-8");
  const lines = content.split("\n").slice(1); // skip header
  const map = {};
  for (const line of lines) {
    const parts = line.split(",");
    if (parts.length >= 4) {
      const ticker = (parts[0] || "").trim().padStart(6, "0");
      const tier1 = (parts[3] || "").trim();
      if (ticker && tier1) map[ticker] = tier1;
    }
  }
  return map;
}

// ============================================================
// 폴더명 안전 변환 (특수문자 제거)
// ============================================================
function safeFolderName(name) {
  return name.replace(/[<>:"/\\|?*]/g, "_");
}

// ============================================================
// 단일 리포트 생성
// ============================================================
async function generateSingleReport(analysisPath, sectorMap) {
  const raw = fs.readFileSync(analysisPath, "utf-8");
  const analysis = JSON.parse(raw);

  const ticker = analysis.ticker || "";
  const name = analysis.name || "Unknown";
  const year = analysis.year || "";
  const quarter = analysis.quarter || "";
  const tier1 = sectorMap[ticker] || analysis.sector || "기타";

  // 출력 디렉토리 - RESULT_DIR 또는 CLI에서 지정한 --outdir 사용
  const effectiveResultDir = global.__OUTDIR__ || RESULT_DIR;
  const outDir = path.join(
    effectiveResultDir,
    safeFolderName(tier1),
    String(year),
    quarter
  );
  fs.mkdirSync(outDir, { recursive: true });

  const outPath = path.join(outDir, `${name}_분석보고서.docx`);

  // docx 생성
  const doc = buildReport(analysis);
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outPath, buffer);

  console.log(`  OK ${name} -> ${tier1}/${year}/${quarter}/`);
  return outPath;
}

// ============================================================
// 배치 생성
// ============================================================
async function generateAll(year, quarter, sector, inputFile) {
  console.log("=".repeat(60));
  console.log("PHASE5 Report - Step 3: docx report generation");
  console.log(`  Target: ${year} ${quarter}`);
  console.log("=".repeat(60));

  const sectorMap = loadSectorMap();

  // 단일 파일
  if (inputFile) {
    const outPath = await generateSingleReport(inputFile, sectorMap);
    console.log(`\nDone: ${outPath}`);
    return;
  }

  // 배치: cache에서 analysis JSON 파일들 탐색
  const cacheFiles = fs
    .readdirSync(CACHE_DIR)
    .filter((f) => f.endsWith(`_${year}_${quarter}_analysis.json`));

  if (cacheFiles.length === 0) {
    console.log(`[ERROR] No analysis results for ${year} ${quarter}`);
    return;
  }

  let success = 0;
  let fail = 0;

  for (const fname of cacheFiles) {
    const ticker = fname.split("_")[0];

    // 섹터 필터
    if (sector && sectorMap[ticker] !== sector) continue;

    try {
      await generateSingleReport(path.join(CACHE_DIR, fname), sectorMap);
      success++;
    } catch (e) {
      console.log(`  FAIL ${fname}: ${e.message}`);
      fail++;
    }
  }

  console.log(`\n${"=".repeat(60)}`);
  console.log(`Done: success ${success}, fail ${fail}`);
  console.log(`Output: ${RESULT_DIR}`);
  console.log("=".repeat(60));
}

// ============================================================
// CLI
// ============================================================
const args = process.argv.slice(2);
const parseArg = (flag) => {
  const idx = args.indexOf(flag);
  return idx >= 0 && idx + 1 < args.length ? args[idx + 1] : null;
};

const year = parseArg("--year") || String(new Date().getFullYear() - 1);
const quarter = (parseArg("--quarter") || "4Q").toUpperCase();
const sector = parseArg("--sector") || null;
const inputFile = parseArg("--input") || null;
const outdir = parseArg("--outdir") || null;
if (outdir) global.__OUTDIR__ = outdir;

generateAll(year, quarter, sector, inputFile).catch((e) => {
  console.error("Error:", e);
  process.exit(1);
});
