using System;
using System.Text.Json;
using System.Threading.Tasks;

namespace SimCore.Cache
{
    /// <summary>
    /// In-memory cache fallback when Redis is not available
    /// Can be upgraded to Redis with IConnectionMultiplexer
    /// </summary>
    public static class SimulationCache
    {
        private static System.Collections.Concurrent.ConcurrentDictionary<string, CacheEntry> _memoryCache 
            = new System.Collections.Concurrent.ConcurrentDictionary<string, CacheEntry>();
        
        private static bool _useRedis = false;
        // private static IConnectionMultiplexer _redis;
        // private static IDatabase _redisDb;
        
        /// <summary>
        /// Initialize cache (in-memory or Redis)
        /// </summary>
        public static void Initialize(string connectionString = null)
        {
            if (!string.IsNullOrEmpty(connectionString) && connectionString.Contains(":"))
            {
                // Redis would be initialized here
                // _redis = ConnectionMultiplexer.Connect(connectionString);
                // _redisDb = _redis.GetDatabase();
                // _useRedis = true;
                Console.WriteLine("[Cache] Redis connection would be initialized here");
                _useRedis = false; // Fallback to memory for now
            }
            else
            {
                Console.WriteLine("[Cache] Using in-memory cache");
                _useRedis = false;
            }
        }
        
        /// <summary>
        /// Get value from cache
        /// </summary>
        public static async Task<T> GetAsync<T>(string key)
        {
            var fullKey = $"sator:sim:{key}";
            
            if (_useRedis)
            {
                // Redis implementation
                // var data = await _redisDb.StringGetAsync(fullKey);
                // if (data.IsNullOrEmpty) return default;
                // return JsonSerializer.Deserialize<T>(data);
            }
            
            // In-memory fallback
            if (_memoryCache.TryGetValue(fullKey, out var entry))
            {
                if (entry.Expiry > DateTime.UtcNow)
                {
                    Console.WriteLine($"[Cache] HIT: {key}");
                    return JsonSerializer.Deserialize<T>(entry.Data);
                }
                else
                {
                    _memoryCache.TryRemove(fullKey, out _);
                }
            }
            
            Console.WriteLine($"[Cache] MISS: {key}");
            return default;
        }
        
        /// <summary>
        /// Set value in cache
        /// </summary>
        public static async Task SetAsync<T>(string key, T value, TimeSpan? expiry = null)
        {
            var fullKey = $"sator:sim:{key}";
            var data = JsonSerializer.Serialize(value);
            var expiration = DateTime.UtcNow.Add(expiry ?? TimeSpan.FromHours(1));
            
            if (_useRedis)
            {
                // await _redisDb.StringSetAsync(fullKey, data, expiry);
            }
            else
            {
                _memoryCache[fullKey] = new CacheEntry { Data = data, Expiry = expiration };
                Console.WriteLine($"[Cache] SET: {key} (expires: {expiration:HH:mm:ss})");
            }
        }
        
        /// <summary>
        /// Check if key exists
        /// </summary>
        public static async Task<bool> ExistsAsync(string key)
        {
            var fullKey = $"sator:sim:{key}";
            
            if (_useRedis)
            {
                // return await _redisDb.KeyExistsAsync(fullKey);
                return false;
            }
            
            return _memoryCache.ContainsKey(fullKey) && _memoryCache[fullKey].Expiry > DateTime.UtcNow;
        }
        
        /// <summary>
        /// Remove key from cache
        /// </summary>
        public static async Task RemoveAsync(string key)
        {
            var fullKey = $"sator:sim:{key}";
            
            if (_useRedis)
            {
                // await _redisDb.KeyDeleteAsync(fullKey);
            }
            else
            {
                _memoryCache.TryRemove(fullKey, out _);
            }
        }
        
        /// <summary>
        /// Clear all cached data
        /// </summary>
        public static void Clear()
        {
            _memoryCache.Clear();
            Console.WriteLine("[Cache] Cleared all entries");
        }
        
        /// <summary>
        /// Get cache statistics
        /// </summary>
        public static object GetStats()
        {
            return new
            {
                EntryCount = _memoryCache.Count,
                UsingRedis = _useRedis
            };
        }
        
        private class CacheEntry
        {
            public string Data { get; set; }
            public DateTime Expiry { get; set; }
        }
    }
}