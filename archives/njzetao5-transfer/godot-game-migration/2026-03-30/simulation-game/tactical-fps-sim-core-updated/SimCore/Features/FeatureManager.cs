using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

namespace SimCore.Features
{
    /// <summary>
    /// Feature flag configuration
    /// </summary>
    public class FeatureConfig
    {
        public bool Enabled { get; set; }
        public string Description { get; set; }
        public int RolloutPercentage { get; set; }
        public List<string> AllowedUsers { get; set; } = new List<string>();
    }
    
    /// <summary>
    /// Feature flag data structure
    /// </summary>
    public class FeatureData
    {
        public Dictionary<string, FeatureConfig> Features { get; set; } = new();
    }
    
    /// <summary>
    /// Manages feature flags for simulation experiments
    /// </summary>
    public static class FeatureManager
    {
        private static FeatureData _data = new FeatureData();
        private static string _configPath = "Defs/features.json";
        private static DateTime _lastLoadTime = DateTime.MinValue;
        
        /// <summary>
        /// Initialize feature manager
        /// </summary>
        public static void Initialize(string configPath = null)
        {
            if (configPath != null)
                _configPath = configPath;
            
            Reload();
        }
        
        /// <summary>
        /// Reload configuration from file
        /// </summary>
        public static void Reload()
        {
            try
            {
                if (File.Exists(_configPath))
                {
                    var json = File.ReadAllText(_configPath);
                    _data = JsonSerializer.Deserialize<FeatureData>(json) ?? new FeatureData();
                    _lastLoadTime = DateTime.UtcNow;
                    Console.WriteLine($"[Features] Loaded {_data.Features.Count} features from {_configPath}");
                }
                else
                {
                    Console.WriteLine($"[Features] Config not found: {_configPath}");
                    _data = new FeatureData();
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[Features] Error loading config: {ex.Message}");
                _data = new FeatureData();
            }
        }
        
        /// <summary>
        /// Check if feature is enabled for user
        /// </summary>
        public static bool IsEnabled(string featureName, string userId = null)
        {
            // Auto-reload if file changed (simple check)
            if (File.Exists(_configPath) && File.GetLastWriteTimeUtc(_configPath) > _lastLoadTime)
            {
                Reload();
            }
            
            if (!_data.Features.TryGetValue(featureName, out var config))
            {
                return false; // Unknown features default to disabled
            }
            
            // Check if explicitly disabled
            if (!config.Enabled)
                return false;
            
            // Check if fully enabled
            if (config.RolloutPercentage >= 100)
                return true;
            
            // Check user-specific allowlist
            if (userId != null && config.AllowedUsers.Contains(userId))
                return true;
            
            // Percentage-based rollout using hash
            if (userId != null)
            {
                var hash = Math.Abs(userId.GetHashCode()) % 100;
                return hash < config.RolloutPercentage;
            }
            
            // No user ID and not fully rolled out
            return false;
        }
        
        /// <summary>
        /// Get feature configuration
        /// </summary>
        public static FeatureConfig GetConfig(string featureName)
        {
            _data.Features.TryGetValue(featureName, out var config);
            return config;
        }
        
        /// <summary>
        /// List all features
        /// </summary>
        public static Dictionary<string, FeatureConfig> GetAllFeatures()
        {
            return new Dictionary<string, FeatureConfig>(_data.Features);
        }
        
        /// <summary>
        /// List enabled features for user
        /// </summary>
        public static List<string> GetEnabledFeatures(string userId = null)
        {
            var enabled = new List<string>();
            foreach (var feature in _data.Features.Keys)
            {
                if (IsEnabled(feature, userId))
                    enabled.Add(feature);
            }
            return enabled;
        }
    }
}