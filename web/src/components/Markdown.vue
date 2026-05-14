<script setup lang="ts">
import { computed, h, defineComponent, type PropType } from "vue";

const props = withDefaults(
  defineProps<{
    content: string;
    highlightTerms?: string[];
    streaming?: boolean;
  }>(),
  { highlightTerms: () => [], streaming: false },
);

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

type BlockNode =
  | { type: "code"; lang: string; content: string }
  | { type: "heading"; level: number; content: string }
  | { type: "hr" }
  | { type: "list"; ordered: boolean; items: string[] }
  | { type: "paragraph"; content: string };

type InlineNode =
  | { type: "text"; content: string }
  | { type: "code"; content: string }
  | { type: "bold"; content: string }
  | { type: "italic"; content: string }
  | { type: "link"; text: string; href: string }
  | { type: "br" };

/* ------------------------------------------------------------------ */
/*  Block parser                                                       */
/* ------------------------------------------------------------------ */

function parseBlocks(text: string): BlockNode[] {
  const lines = text.split("\n");
  const blocks: BlockNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    const fenceMatch = line.match(/^```(\w*)/);
    if (fenceMatch) {
      const lang = fenceMatch[1] || "";
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++;
      blocks.push({ type: "code", lang, content: codeLines.join("\n") });
      continue;
    }

    const headingMatch = line.match(/^(#{1,4})\s+(.+)/);
    if (headingMatch) {
      blocks.push({
        type: "heading",
        level: headingMatch[1].length,
        content: headingMatch[2],
      });
      i++;
      continue;
    }

    if (/^[-*_]{3,}\s*$/.test(line)) {
      blocks.push({ type: "hr" });
      i++;
      continue;
    }

    if (/^[-*+]\s/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*+]\s/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*+]\s/, ""));
        i++;
      }
      blocks.push({ type: "list", ordered: false, items });
      continue;
    }

    if (/^\d+[.)]\s/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+[.)]\s/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+[.)]\s/, ""));
        i++;
      }
      blocks.push({ type: "list", ordered: true, items });
      continue;
    }

    if (line.trim() === "") {
      i++;
      continue;
    }

    const paraLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !lines[i].match(/^```/) &&
      !lines[i].match(/^#{1,4}\s/) &&
      !lines[i].match(/^[-*+]\s/) &&
      !lines[i].match(/^\d+[.)]\s/) &&
      !lines[i].match(/^[-*_]{3,}\s*$/)
    ) {
      paraLines.push(lines[i]);
      i++;
    }
    if (paraLines.length > 0) {
      blocks.push({ type: "paragraph", content: paraLines.join("\n") });
    }
  }

  return blocks;
}

/* ------------------------------------------------------------------ */
/*  Inline parser                                                      */
/* ------------------------------------------------------------------ */

function parseInline(text: string): InlineNode[] {
  const nodes: InlineNode[] = [];
  const pattern =
    /(`[^`]+`)|(\[([^\]]+)\]\(([^)]+)\))|(\*\*([^*]+)\*\*)|(\*([^*]+)\*)|(\bhttps?:\/\/[^\s<>)\]]+)|(\n)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      nodes.push({ type: "text", content: text.slice(lastIndex, match.index) });
    }

    if (match[1]) {
      nodes.push({ type: "code", content: match[1].slice(1, -1) });
    } else if (match[2]) {
      nodes.push({ type: "link", text: match[3], href: match[4] });
    } else if (match[5]) {
      nodes.push({ type: "bold", content: match[6] });
    } else if (match[7]) {
      nodes.push({ type: "italic", content: match[8] });
    } else if (match[9]) {
      nodes.push({ type: "link", text: match[9], href: match[9] });
    } else if (match[10]) {
      nodes.push({ type: "br" });
    }

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    nodes.push({ type: "text", content: text.slice(lastIndex) });
  }

  return nodes;
}

/* ------------------------------------------------------------------ */
/*  Highlight helper                                                    */
/* ------------------------------------------------------------------ */

function highlightParts(text: string, terms: string[]): string[] {
  if (!terms || terms.length === 0) return [text];
  const escaped = terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const regex = new RegExp(`(${escaped.join("|")})`, "gi");
  return text.split(regex);
}

/* ------------------------------------------------------------------ */
/*  Computed                                                            */
/* ------------------------------------------------------------------ */

const blocks = computed(() => parseBlocks(props.content));

/* ------------------------------------------------------------------ */
/*  Sub-components (locally registered)                                  */
/* ------------------------------------------------------------------ */

const StreamingCaret = defineComponent({
  render() {
    return h("span", {
      "aria-hidden": true,
      class:
        "inline-block w-[0.5em] h-[1em] ml-0.5 align-[-0.15em] bg-foreground/50 animate-pulse",
    });
  },
});

const InlineContent = defineComponent({
  props: {
    text: { type: String, required: true },
    highlightTerms: { type: Array as PropType<string[]>, default: () => [] },
  },
  setup(compProps) {
    return () => {
      const nodes = parseInline(compProps.text);
      return nodes.map((node, i) => {
        switch (node.type) {
          case "text":
            return renderHighlighted(node.content, compProps.highlightTerms ?? [], i);
          case "code":
            return h(
              "code",
              {
                key: i,
                class:
                  "bg-secondary/60 px-1.5 py-0.5 text-xs font-mono text-primary/90",
              },
              node.content,
            );
          case "bold":
            return h(
              "strong",
              { key: i, class: "font-semibold" },
              renderHighlighted(node.content, compProps.highlightTerms ?? []),
            );
          case "italic":
            return h(
              "em",
              { key: i },
              renderHighlighted(node.content, compProps.highlightTerms ?? []),
            );
          case "link":
            return h(
              "a",
              {
                key: i,
                href: node.href,
                target: "_blank",
                rel: "noreferrer",
                class:
                  "text-primary underline underline-offset-2 decoration-primary/30 hover:decoration-primary/60 transition-colors",
              },
              node.text,
            );
          case "br":
            return h("br", { key: i });
        }
      });
    };
  },
});

function renderHighlighted(
  text: string,
  terms: string[],
  baseKey?: string | number,
) {
  if (!terms || terms.length === 0) return text;
  const parts = highlightParts(text, terms);
  const escaped = terms.map((t) =>
    t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
  );
  const regex = new RegExp(`(${escaped.join("|")})`, "gi");
  return parts.map((part, j) => {
    const k = baseKey !== undefined ? `${baseKey}-${j}` : j;
    return regex.test(part)
      ? h(
          "mark",
          { key: k, class: "bg-warning/30 text-warning px-0.5" },
          part,
        )
      : h("span", { key: k }, part);
  });
}
</script>

<template>
  <div class="text-sm text-foreground leading-relaxed space-y-2">
    <template v-for="(block, i) in blocks" :key="i">
      <pre
        v-if="block.type === 'code'"
        class="bg-secondary/60 border border-border px-3 py-2.5 text-xs font-mono leading-relaxed overflow-x-auto"
      >
        <code>{{ block.content }}<StreamingCaret v-if="streaming && i === blocks.length - 1" /></code>
      </pre>

      <h2
        v-else-if="block.type === 'heading' && block.level === 1"
        class="text-base font-bold"
      >
        <InlineContent :text="block.content" :highlight-terms="highlightTerms" />
        <StreamingCaret v-if="streaming && i === blocks.length - 1" />
      </h2>
      <h3
        v-else-if="block.type === 'heading' && block.level === 2"
        class="text-sm font-bold"
      >
        <InlineContent :text="block.content" :highlight-terms="highlightTerms" />
        <StreamingCaret v-if="streaming && i === blocks.length - 1" />
      </h3>
      <h4
        v-else-if="block.type === 'heading' && block.level === 3"
        class="text-sm font-semibold"
      >
        <InlineContent :text="block.content" :highlight-terms="highlightTerms" />
        <StreamingCaret v-if="streaming && i === blocks.length - 1" />
      </h4>
      <h5
        v-else-if="block.type === 'heading' && block.level >= 4"
        class="text-sm font-medium"
      >
        <InlineContent :text="block.content" :highlight-terms="highlightTerms" />
        <StreamingCaret v-if="streaming && i === blocks.length - 1" />
      </h5>

      <template v-else-if="block.type === 'hr'">
        <hr class="border-border" />
        <StreamingCaret v-if="streaming && i === blocks.length - 1" />
      </template>

      <ul
        v-else-if="block.type === 'list' && !block.ordered"
        class="space-y-0.5 list-disc pl-5 text-sm"
      >
        <li v-for="(item, j) in block.items" :key="j">
          <InlineContent :text="item" :highlight-terms="highlightTerms" />
          <StreamingCaret
            v-if="
              streaming &&
              i === blocks.length - 1 &&
              j === block.items.length - 1
            "
          />
        </li>
      </ul>

      <ol
        v-else-if="block.type === 'list' && block.ordered"
        class="space-y-0.5 list-decimal pl-5 text-sm"
      >
        <li v-for="(item, j) in block.items" :key="j">
          <InlineContent :text="item" :highlight-terms="highlightTerms" />
          <StreamingCaret
            v-if="
              streaming &&
              i === blocks.length - 1 &&
              j === block.items.length - 1
            "
          />
        </li>
      </ol>

      <p v-else-if="block.type === 'paragraph'">
        <InlineContent :text="block.content" :highlight-terms="highlightTerms" />
        <StreamingCaret v-if="streaming && i === blocks.length - 1" />
      </p>
    </template>

    <StreamingCaret v-if="streaming && blocks.length === 0" />
  </div>
</template>
