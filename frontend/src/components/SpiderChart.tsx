import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface SpiderChartData {
  node_id: string;
  score: number;
}

interface SpiderChartProps {
  data: SpiderChartData[];
  title?: string;
  maxItems?: number;
  height?: number;
  showLegend?: boolean;
  scoreRange?: [number, number];
}

const SpiderChart = ({
  data,
  title = "Performance Overview",
  maxItems = 8,
  height = 400,
  showLegend = true,
  scoreRange = [0, 100],
}: SpiderChartProps) => {
  // Sort by score descending and take top n items
  const processedData = data
    .sort((a, b) => b.score - a.score)
    .slice(0, maxItems)
    .map((item) => ({
      subject: item.node_id,
      score: item.score,
      // Ensure score is within the specified range
      normalizedScore: Math.max(
        scoreRange[0],
        Math.min(scoreRange[1], item.score)
      ),
    }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-lg">
          <p className="font-semibold text-gray-900 dark:text-gray-100">
            {label}
          </p>
          <p className="text-blue-600 dark:text-blue-400">
            Score: {payload[0].value.toFixed(1)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-center text-xl">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Spider Chart */}
          <div className="flex flex-col">
            <ResponsiveContainer width="100%" height={height}>
              <RadarChart
                data={processedData}
                margin={{ top: 20, right: 30, bottom: 20, left: 30 }}
              >
                <PolarGrid gridType="polygon" stroke="#e5e7eb" />
                <PolarAngleAxis
                  dataKey="subject"
                  tick={{
                    fontSize: 12,
                    fill: "#374151",
                    textAnchor: "middle",
                  }}
                />
                <PolarRadiusAxis
                  angle={90}
                  domain={scoreRange}
                  tick={{
                    fontSize: 10,
                    fill: "#6b7280",
                  }}
                  tickCount={5}
                />
                <Radar
                  name="Score"
                  dataKey="normalizedScore"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.1}
                  strokeWidth={2}
                  dot={{
                    r: 4,
                    fill: "#3b82f6",
                    strokeWidth: 2,
                    stroke: "#ffffff",
                  }}
                />
                <Tooltip content={<CustomTooltip />} />
                {showLegend && (
                  <Legend
                    wrapperStyle={{
                      fontSize: "12px",
                      color: "#374151",
                    }}
                  />
                )}
              </RadarChart>
            </ResponsiveContainer>
            {data.length > maxItems && (
              <p className="text-sm text-muted-foreground text-center mt-2">
                Showing top {maxItems} of {data.length} metrics in chart
              </p>
            )}
          </div>

          {/* Data Table */}
          <div className="flex flex-col">
            <div
              className="border rounded-lg overflow-hidden"
              style={{ height: height }}
            >
              <div className="overflow-y-auto h-full">
                <Table>
                  <TableHeader className="sticky top-0 bg-muted/50">
                    <TableRow>
                      <TableHead className="font-semibold">
                        Skill/Area
                      </TableHead>
                      <TableHead className="text-right font-semibold">
                        Score
                      </TableHead>
                      <TableHead className="text-right font-semibold">
                        Rank
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data
                      .sort((a, b) => b.score - a.score)
                      .map((item, index) => (
                        <TableRow
                          key={item.node_id}
                          className={
                            index < maxItems
                              ? "bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800"
                              : ""
                          }
                        >
                          <TableCell className="font-medium">
                            {item.node_id}
                            {index < maxItems && (
                              <span className="ml-2 text-xs text-blue-600 dark:text-blue-400">
                                (in chart)
                              </span>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            <span
                              className={`font-semibold ${
                                item.score >= 80
                                  ? "text-green-600 dark:text-green-400"
                                  : item.score >= 60
                                  ? "text-yellow-600 dark:text-yellow-400"
                                  : "text-red-600 dark:text-red-400"
                              }`}
                            >
                              {item.score.toFixed(1)}
                            </span>
                          </TableCell>
                          <TableCell className="text-right text-muted-foreground">
                            #{index + 1}
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </div>
            </div>
            <p className="text-xs text-muted-foreground text-center mt-2">
              Total: {data.length} skills assessed
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default SpiderChart;
