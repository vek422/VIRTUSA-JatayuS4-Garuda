import React, { useMemo } from "react";
import Tree from "react-d3-tree";

function convertToTreeData(root_nodes: any[]): any[] {
  return root_nodes.map((node) => ({
    name: node.skill,
    attributes: node.priority ? { priority: node.priority } : undefined,
    children:
      node.subskills && node.subskills.length > 0
        ? convertToTreeData(node.subskills)
        : undefined,
  }));
}

export interface SkillTreeGraphProps {
  root_nodes: any[];
}

const containerStyles: React.CSSProperties = {
  width: "100%",
  height: "600px",
  background: "#ffffff",
  borderRadius: 8,
  border: "1px solid #e2e8f0",
  marginTop: 16,
};

const SkillGraphTree: React.FC<SkillTreeGraphProps> = ({ root_nodes }) => {
  const data = useMemo(
    () => [
      {
        name: "Skill Graph",
        children: convertToTreeData(root_nodes),
      },
    ],
    [root_nodes]
  );

  if (!root_nodes || root_nodes.length === 0) {
    return (
      <div className="text-center text-muted-foreground">
        No skill tree data available.
      </div>
    );
  }
  return (
    <div
      style={containerStyles}
      className="bg-white border border-gray-200 rounded-lg shadow-sm"
    >
      <Tree
        data={data}
        orientation="vertical"
        translate={{ x: 400, y: 80 }}
        collapsible={false}
        pathFunc="elbow"
        zoomable={true}
        separation={{ siblings: 1.8, nonSiblings: 2.2 }}
        nodeSize={{ x: 150, y: 120 }}
        renderCustomNodeElement={({ nodeDatum }) => (
          <g fontFamily="'Inter', 'Segoe UI', Arial, sans-serif">
            <circle r={18} fill="#3b82f6" />
            <text
              fill="#0f172a"
              fontWeight={600}
              fontSize={14}
              x={0}
              y={-35}
              textAnchor="middle"
              style={{ pointerEvents: "none" }}
            >
              {nodeDatum.name}
            </text>
            {nodeDatum.attributes && nodeDatum.attributes.priority && (
              <text
                x={0}
                y={-18}
                fontSize={11}
                fill="#64748b"
                fontWeight={500}
                textAnchor="middle"
                style={{ pointerEvents: "none" }}
              >
                Priority: {nodeDatum.attributes.priority}
              </text>
            )}
          </g>
        )}
        pathClassFunc={() => "tree-link"}
      />
      <style>{`
        .tree-link {
          stroke: #94a3b8;
          stroke-width: 2px;
          fill: none;
        }
        .tree-link:hover {
          stroke: #475569;
          stroke-width: 3px;
        }
      `}</style>
    </div>
  );
};

export default SkillGraphTree;
