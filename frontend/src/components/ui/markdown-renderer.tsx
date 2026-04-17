import { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import type { Components } from "react-markdown";
import { CopyButton } from "./copy-button";

export type MarkdownVariant = "compact" | "document";

interface MarkdownRendererProps {
  content: string;
  className?: string;
  variant?: MarkdownVariant;
}

function extractLanguage(className: string | undefined): string {
  if (!className) return "";
  const match = className.match(/language-(\w+)/);
  return match ? match[1] : "";
}

export function headingSlug(children: React.ReactNode): string {
  const text = typeof children === "string"
    ? children
    : Array.isArray(children)
      ? children.map((c) => (typeof c === "string" ? c : "")).join("")
      : String(children ?? "");
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .replace(/\s+/g, "-");
}

const HEADING_STYLES: Record<MarkdownVariant, Record<string, string>> = {
  compact: {
    h1: "text-lg font-semibold text-primary mt-4 mb-2",
    h2: "text-base font-semibold text-primary mt-3 mb-1.5",
    h3: "text-sm font-semibold text-primary mt-2.5 mb-1",
    h4: "text-sm font-medium text-secondary mt-2 mb-1",
    h5: "text-xs font-medium text-secondary mt-1.5 mb-0.5",
    h6: "text-xs font-medium text-secondary mt-1.5 mb-0.5",
    p: "leading-relaxed text-secondary my-1.5",
    ul: "list-disc list-outside pl-5 space-y-0.5 my-1.5 text-secondary",
    ol: "list-decimal list-outside pl-5 space-y-0.5 my-1.5 text-secondary",
    li: "leading-relaxed [&>p]:my-0 [&>p]:inline",
    blockquote: "border-l-2 border-hover pl-3 my-2 italic text-muted",
  },
  document: {
    h1: "text-2xl font-bold text-primary mt-8 mb-3 first:mt-0",
    h2: "text-xl font-bold text-primary mt-7 mb-2.5",
    h3: "text-lg font-semibold text-primary mt-5 mb-2",
    h4: "text-base font-semibold text-primary mt-4 mb-1.5",
    h5: "text-sm font-medium text-secondary mt-3 mb-1",
    h6: "text-sm font-medium text-secondary mt-3 mb-1",
    p: "text-[15px] leading-[1.75] text-secondary my-2.5",
    ul: "list-disc list-outside pl-6 space-y-1.5 my-3 text-secondary text-[15px] leading-[1.75]",
    ol: "list-decimal list-outside pl-6 space-y-1.5 my-3 text-secondary text-[15px] leading-[1.75]",
    li: "leading-[1.75] [&>p]:my-0 [&>p]:inline",
    blockquote: "border-l-3 border-hover pl-4 my-4 italic text-muted",
  },
};

function MarkdownRendererInner({ content, className = "", variant = "compact" }: MarkdownRendererProps) {
  const s = HEADING_STYLES[variant];
  const components: Components = {
    h1: ({ children }) => (
      <h1 id={headingSlug(children)} className={s.h1}>{children}</h1>
    ),
    h2: ({ children }) => (
      <h2 id={headingSlug(children)} className={s.h2}>{children}</h2>
    ),
    h3: ({ children }) => (
      <h3 id={headingSlug(children)} className={s.h3}>{children}</h3>
    ),
    h4: ({ children }) => (
      <h4 id={headingSlug(children)} className={s.h4}>{children}</h4>
    ),
    h5: ({ children }) => (
      <h5 id={headingSlug(children)} className={s.h5}>{children}</h5>
    ),
    h6: ({ children }) => (
      <h6 id={headingSlug(children)} className={s.h6}>{children}</h6>
    ),
    p: ({ children }) => (
      <p className={s.p}>{children}</p>
    ),
    a: ({ href, children }) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-accent-cyan hover:text-accent-cyan hover:bg-control/30 rounded px-0.5 -mx-0.5 underline underline-offset-2 transition"
      >
        {children}
      </a>
    ),
    strong: ({ children }) => (
      <strong className="font-semibold text-primary">{children}</strong>
    ),
    em: ({ children }) => (
      <em className="italic text-secondary">{children}</em>
    ),
    code: ({ className: codeClassName, children }) => {
      const lang = extractLanguage(codeClassName);
      const hasHljsClass = codeClassName?.includes("hljs");
      const isBlock = lang || hasHljsClass;
      if (!isBlock) {
        return (
          <code className="px-1.5 py-0.5 rounded bg-control/80 text-accent-cyan text-[12px] font-mono">
            {children}
          </code>
        );
      }
      return (
        <code className={`${codeClassName || ""} text-[12px] font-mono`}>
          {children}
        </code>
      );
    },
    pre: ({ children }) => {
      const codeChild = children as React.ReactElement<{
        className?: string;
        children?: unknown;
      }>;
      const lang = extractLanguage(codeChild?.props?.className);
      const codeText = extractCodeText(codeChild);

      return (
        <div className="my-2 rounded-lg border border-card overflow-hidden">
          <div className="flex items-center justify-between px-3 py-1.5 bg-control/80 border-b border-card">
            <span className="text-[10px] font-medium text-muted uppercase tracking-wider">
              {lang || "code"}
            </span>
            <CopyButton text={codeText} />
          </div>
          <pre className="p-3 overflow-x-auto bg-panel/30 text-[12px] leading-relaxed !m-0">
            {children}
          </pre>
        </div>
      );
    },
    ul: ({ children }) => (
      <ul className={s.ul}>{children}</ul>
    ),
    ol: ({ children }) => (
      <ol className={s.ol}>{children}</ol>
    ),
    li: ({ children }) => (
      <li className={s.li}>{children}</li>
    ),
    blockquote: ({ children }) => (
      <blockquote className={s.blockquote}>
        {children}
      </blockquote>
    ),
    table: ({ children }) => (
      <div className="my-2 overflow-x-auto rounded-lg border border-card">
        <table className="w-full text-[12px]">{children}</table>
      </div>
    ),
    thead: ({ children }) => (
      <thead className="bg-panel text-secondary">{children}</thead>
    ),
    tr: ({ children }) => (
      <tr className="border-b border-card">{children}</tr>
    ),
    th: ({ children }) => (
      <th className="px-3 py-1.5 text-left font-medium text-secondary">{children}</th>
    ),
    td: ({ children }) => (
      <td className="px-3 py-1.5 text-muted">{children}</td>
    ),
    hr: () => <hr className="border-card my-3" />,
  };

  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

function extractCodeText(codeChild: React.ReactElement<{ children?: unknown }> | null): string {
  if (!codeChild?.props?.children) return "";
  const raw = codeChild.props.children;
  if (typeof raw === "string") return raw.replace(/\n$/, "");
  if (Array.isArray(raw)) return (raw as unknown[]).map(String).join("").replace(/\n$/, "");
  return String(raw).replace(/\n$/, "");
}

export const MarkdownRenderer = memo(MarkdownRendererInner);
