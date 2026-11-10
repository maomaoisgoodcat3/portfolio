import type { ComponentProps } from "react";
import type { Block } from "@/lib/api";
import { BlockEditor } from "./BlockEditor";

type Props = {
  blocks: Block[];
  onUpdate: BlockEditorProps["onUpdate"];
  onDelete: BlockEditorProps["onDelete"];
  onAddItem: BlockEditorProps["onAddItem"];
  onUpdateItem: BlockEditorProps["onUpdateItem"];
  onDeleteItem: BlockEditorProps["onDeleteItem"];
  onMove: (id: string, direction: -1 | 1) => Promise<void>;
};

type BlockEditorProps = ComponentProps<typeof BlockEditor>;

export function BlockList({ blocks, onUpdate, onDelete, onAddItem, onUpdateItem, onDeleteItem, onMove }: Props) {
  return (
    <div className="space-y-4">
      {blocks.map((block, index) => (
        <div key={block.id}>
          <div className="mb-2 flex gap-3 text-sm">
            <button disabled={index === 0} onClick={() => void onMove(block.id, -1)}>Move up</button>
            <button disabled={index === blocks.length - 1} onClick={() => void onMove(block.id, 1)}>Move down</button>
          </div>
          <BlockEditor block={block} onUpdate={onUpdate} onDelete={onDelete} onAddItem={onAddItem} onUpdateItem={onUpdateItem} onDeleteItem={onDeleteItem} />
        </div>
      ))}
    </div>
  );
}
