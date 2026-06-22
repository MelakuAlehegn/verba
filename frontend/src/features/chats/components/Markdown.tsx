import type { ComponentPropsWithoutRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// Element overrides so LLM Markdown is styled without the typography plugin.
const COMPONENTS = {
  p: (props: ComponentPropsWithoutRef<"p">) => <p className="mb-3 leading-relaxed last:mb-0" {...props} />,
  ul: (props: ComponentPropsWithoutRef<"ul">) => (
    <ul className="mb-3 list-disc space-y-1 pl-5 last:mb-0" {...props} />
  ),
  ol: (props: ComponentPropsWithoutRef<"ol">) => (
    <ol className="mb-3 list-decimal space-y-1 pl-5 last:mb-0" {...props} />
  ),
  a: (props: ComponentPropsWithoutRef<"a">) => (
    <a className="font-medium text-primary underline underline-offset-2" target="_blank" rel="noreferrer" {...props} />
  ),
  h1: (props: ComponentPropsWithoutRef<"h1">) => <h3 className="mb-2 mt-4 text-lg font-semibold first:mt-0" {...props} />,
  h2: (props: ComponentPropsWithoutRef<"h2">) => <h4 className="mb-2 mt-4 text-base font-semibold first:mt-0" {...props} />,
  h3: (props: ComponentPropsWithoutRef<"h3">) => <h5 className="mb-2 mt-3 font-semibold first:mt-0" {...props} />,
  blockquote: (props: ComponentPropsWithoutRef<"blockquote">) => (
    <blockquote className="mb-3 border-l-2 border-border pl-3 text-muted-foreground" {...props} />
  ),
  pre: (props: ComponentPropsWithoutRef<"pre">) => (
    <pre className="mb-3 overflow-x-auto rounded-lg bg-muted p-3 text-sm last:mb-0" {...props} />
  ),
  code: ({ className, ...props }: ComponentPropsWithoutRef<"code">) =>
    className?.includes("language-") ? (
      // Fenced block — let <pre> own the styling.
      <code className={className} {...props} />
    ) : (
      <code className="rounded bg-muted px-1.5 py-0.5 text-[0.85em]" {...props} />
    ),
};

export function Markdown({ content }: { content: string }) {
  return (
    <div className="text-sm">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={COMPONENTS}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
