using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Collections.Generic;
using SimCore.Resilience;
using SimCore.Cache;

namespace SimCore.Api
{
    /// <summary>
    /// Async HTTP client for SATOR API with connection pooling and circuit breaker
    /// </summary>
    public class SatorApiClient : IDisposable
    {
        private readonly HttpClient _httpClient;
        private readonly string _baseUrl;
        private readonly CircuitBreaker _circuitBreaker;
        
        public SatorApiClient(string baseUrl, string apiKey = null)
        {
            _baseUrl = baseUrl;
            _circuitBreaker = new CircuitBreaker("sator_api", failureThreshold: 3, recoveryTimeoutSeconds: 60);
            
            // Connection pooling configuration
            var handler = new SocketsHttpHandler
            {
                PooledConnectionLifetime = TimeSpan.FromMinutes(5),
                MaxConnectionsPerServer = 20,
                EnableMultipleHttp2Connections = true
            };
            
            _httpClient = new HttpClient(handler)
            {
                BaseAddress = new Uri(baseUrl),
                Timeout = TimeSpan.FromSeconds(30)
            };
            
            if (!string.IsNullOrEmpty(apiKey))
            {
                _httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");
            }
            _httpClient.DefaultRequestHeaders.Add("User-Agent", "RadiantX-Sim/2.0");
        }
        
        /// <summary>
        /// Get player statistics from API with caching
        /// </summary>
        public async Task<PlayerStats> GetPlayerStatsAsync(string playerId)
        {
            // Check circuit breaker
            if (!_circuitBreaker.CanExecute())
            {
                Console.WriteLine($"Circuit open - using cache for player {playerId}");
                return await GetCachedStatsAsync(playerId);
            }
            
            try
            {
                var response = await _httpClient.GetAsync($"/api/players/{playerId}/stats");
                response.EnsureSuccessStatusCode();
                
                var stats = await response.Content.ReadFromJsonAsync<PlayerStats>();
                _circuitBreaker.RecordSuccess();
                
                // Cache the result
                await CacheStatsAsync(playerId, stats);
                
                return stats;
            }
            catch (HttpRequestException ex)
            {
                _circuitBreaker.RecordFailure();
                Console.WriteLine($"API request failed: {ex.Message}");
                return await GetCachedStatsAsync(playerId);
            }
            catch (Exception ex)
            {
                _circuitBreaker.RecordFailure();
                Console.WriteLine($"Unexpected error: {ex.Message}");
                return await GetCachedStatsAsync(playerId);
            }
        }
        
        /// <summary>
        /// Get match data from API
        /// </summary>
        public async Task<MatchData> GetMatchDataAsync(string matchId)
        {
            if (!_circuitBreaker.CanExecute())
            {
                return await SimulationCache.GetAsync<MatchData>($"match:{matchId}") 
                    ?? MatchData.Empty;
            }
            
            try
            {
                var response = await _httpClient.GetAsync($"/api/matches/{matchId}");
                response.EnsureSuccessStatusCode();
                
                var data = await response.Content.ReadFromJsonAsync<MatchData>();
                _circuitBreaker.RecordSuccess();
                
                await SimulationCache.SetAsync($"match:{matchId}", data, TimeSpan.FromHours(1));
                return data;
            }
            catch (Exception ex)
            {
                _circuitBreaker.RecordFailure();
                Console.WriteLine($"Failed to get match data: {ex.Message}");
                return await SimulationCache.GetAsync<MatchData>($"match:{matchId}") 
                    ?? MatchData.Empty;
            }
        }
        
        private async Task<PlayerStats> GetCachedStatsAsync(string playerId)
        {
            var cached = await SimulationCache.GetAsync<PlayerStats>($"player:{playerId}");
            if (cached != null)
            {
                Console.WriteLine($"Cache hit for player {playerId}");
                return cached;
            }
            return PlayerStats.Default;
        }
        
        private async Task CacheStatsAsync(string playerId, PlayerStats stats)
        {
            await SimulationCache.SetAsync($"player:{playerId}", stats, TimeSpan.FromHours(1));
        }
        
        public void Dispose()
        {
            _httpClient?.Dispose();
        }
    }
    
    // Data models
    public class PlayerStats
    {
        public string PlayerId { get; set; }
        public string Name { get; set; }
        public double SimRating { get; set; }
        public double CombatEfficiency { get; set; }
        public double ClutchPerformance { get; set; }
        public double UtilityImpact { get; set; }
        public double EconomicManagement { get; set; }
        public double SpatialControl { get; set; }
        public int MatchesPlayed { get; set; }
        
        public static PlayerStats Default = new PlayerStats
        {
            PlayerId = "unknown",
            Name = "Unknown Player",
            SimRating = 50.0,
            CombatEfficiency = 50.0,
            ClutchPerformance = 50.0,
            UtilityImpact = 50.0,
            EconomicManagement = 50.0,
            SpatialControl = 50.0,
            MatchesPlayed = 0
        };
    }
    
    public class MatchData
    {
        public string MatchId { get; set; }
        public string TeamA { get; set; }
        public string TeamB { get; set; }
        public string Map { get; set; }
        public List<RoundData> Rounds { get; set; } = new();
        
        public static MatchData Empty = new MatchData
        {
            MatchId = "empty",
            TeamA = "Unknown",
            TeamB = "Unknown",
            Map = "Unknown"
        };
    }
    
    public class RoundData
    {
        public int RoundNumber { get; set; }
        public string Winner { get; set; }
        public string BuyTypeA { get; set; }
        public string BuyTypeB { get; set; }
    }
}