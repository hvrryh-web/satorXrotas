using System;
using System.Collections.Generic;
using System.Linq;

namespace SimCore.XAI
{
    /// <summary>
    /// Explainable AI - Transparency tools for belief-based agents
    /// Provides SHAP-like values and attention heatmaps for agent decisions
    /// </summary>
    public static class ExplainableAI
    {
        /// <summary>
        /// Records decision factors for later explanation
        /// </summary>
        public class DecisionContext
        {
            public string DecisionType { get; set; }
            public string AgentId { get; set; }
            public Dictionary<string, double> Features { get; set; } = new();
            public Dictionary<string, double> FeatureWeights { get; set; } = new();
            public double FinalDecisionScore { get; set; }
            public DateTime Timestamp { get; set; } = DateTime.UtcNow;
            public List<string> ReasoningChain { get; set; } = new();
        }
        
        /// <summary>
        /// Calculate feature importance (SHAP-like values)
        /// </summary>
        public static Dictionary<string, double> CalculateFeatureImportance(
            DecisionContext context)
        {
            var importance = new Dictionary<string, double>();
            
            foreach (var feature in context.Features)
            {
                // Calculate marginal contribution
                var weight = context.FeatureWeights.GetValueOrDefault(feature.Key, 1.0);
                var contribution = feature.Value * weight;
                
                // Normalize to percentage
                importance[feature.Key] = contribution;
            }
            
            // Normalize to sum to 100%
            var total = importance.Values.Sum();
            if (total > 0)
            {
                foreach (var key in importance.Keys.ToList())
                {
                    importance[key] = (importance[key] / total) * 100;
                }
            }
            
            return importance.OrderByDescending(x => x.Value).ToDictionary(x => x.Key, x => x.Value);
        }
        
        /// <summary>
        /// Generate human-readable explanation
        /// </summary>
        public static string GenerateExplanation(DecisionContext context)
        {
            var importance = CalculateFeatureImportance(context);
            var topFactors = importance.Take(3);
            
            var explanation = $"Decision: {context.DecisionType}\n";
            explanation += $"Agent: {context.AgentId}\n";
            explanation += $"Confidence: {context.FinalDecisionScore:P}\n\n";
            explanation += "Key Factors:\n";
            
            foreach (var factor in topFactors)
            {
                explanation += $"  • {factor.Key}: {factor.Value:F1}% influence\n";
            }
            
            if (context.ReasoningChain.Any())
            {
                explanation += "\nReasoning:\n";
                foreach (var step in context.ReasoningChain)
                {
                    explanation += $"  → {step}\n";
                }
            }
            
            return explanation;
        }
        
        /// <summary>
        /// Generate attention heatmap data for spatial decisions
        /// </summary>
        public static SpatialHeatmap GenerateAttentionHeatmap(
            string agentId,
            Dictionary<(string x, string y), double> attentionWeights)
        {
            return new SpatialHeatmap
            {
                AgentId = agentId,
                Timestamp = DateTime.UtcNow,
                Points = attentionWeights.Select(w => new HeatmapPoint
                {
                    X = w.Key.x,
                    Y = w.Key.y,
                    Intensity = w.Value
                }).ToList()
            };
        }
        
        /// <summary>
        /// Log decision for audit trail
        /// </summary>
        public static void LogDecision(DecisionContext context)
        {
            // Would write to database or file
            Console.WriteLine($"[XAI] {context.Timestamp:HH:mm:ss} - {context.AgentId} decided {context.DecisionType}");
            Console.WriteLine(GenerateExplanation(context));
        }
    }
    
    /// <summary>
    /// Spatial heatmap for visualizing agent attention
    /// </summary>
    public class SpatialHeatmap
    {
        public string AgentId { get; set; }
        public DateTime Timestamp { get; set; }
        public List<HeatmapPoint> Points { get; set; } = new();
        
        /// <summary>
        /// Export to JSON for visualization
        /// </summary>
        public string ToJson()
        {
            return System.Text.Json.JsonSerializer.Serialize(this, new System.Text.Json.JsonSerializerOptions
            {
                WriteIndented = true
            });
        }
    }
    
    public class HeatmapPoint
    {
        public string X { get; set; }
        public string Y { get; set; }
        public double Intensity { get; set; }
    }
    
    /// <summary>
    /// Integration with Combat System
    /// </summary>
    public static class CombatXAI
    {
        public static ExplainableAI.DecisionContext AnalyzeDuelDecision(
            string agentId,
            bool choseToEngage,
            double enemyDistance,
            double healthRatio,
            double weaponAdvantage,
            double coverAvailability)
        {
            var context = new ExplainableAI.DecisionContext
            {
                DecisionType = choseToEngage ? "Engage" : "Retreat",
                AgentId = agentId,
                Features = new Dictionary<string, double>
                {
                    ["enemy_distance"] = NormalizeDistance(enemyDistance),
                    ["health_ratio"] = healthRatio,
                    ["weapon_advantage"] = weaponAdvantage,
                    ["cover_availability"] = coverAvailability
                },
                FeatureWeights = new Dictionary<string, double>
                {
                    ["enemy_distance"] = 0.3,
                    ["health_ratio"] = 0.35,
                    ["weapon_advantage"] = 0.2,
                    ["cover_availability"] = 0.15
                },
                FinalDecisionScore = choseToEngage ? 0.75 : 0.25,
                ReasoningChain = new List<string>
                {
                    $"Assessed enemy at {enemyDistance:F1}m",
                    $"Health ratio: {healthRatio:P}",
                    $"Weapon advantage: {weaponAdvantage:F2}",
                    choseToEngage ? "Chose to engage" : "Chose to retreat"
                }
            };
            
            ExplainableAI.LogDecision(context);
            return context;
        }
        
        private static double NormalizeDistance(double distance)
        {
            // Normalize 0-50m to 0-1
            return Math.Min(distance / 50.0, 1.0);
        }
    }
}