import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import SkillGraphTree from "./SkillGraphTree";
import { Network } from "lucide-react";

export default function SkillGraphTab({ test }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Skill Graph</CardTitle>
        <CardDescription>
          Visual representation of skills and their relationships
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mt-8">
          {test &&
          test.skill_graph &&
          test.skill_graph.root_nodes &&
          test.skill_graph.root_nodes.length > 0 ? (
            <SkillGraphTree root_nodes={test.skill_graph.root_nodes} />
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Network className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">
                No Skill Graph Data
              </h3>
              <p className="text-muted-foreground mb-4">
                No skill graph data is available for this test. Please check if
                the skill graph has been generated or try again later.
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
