using System;

namespace SimCore.Resilience
{
    /// <summary>
    /// Circuit breaker state
    /// </summary>
    public enum CircuitState 
    { 
        Closed,     // Normal operation
        Open,       // Failing fast
        HalfOpen    // Testing recovery
    }
    
    /// <summary>
    /// Prevents cascade failures by failing fast after threshold
    /// </summary>
    public class CircuitBreaker
    {
        private readonly string _name;
        private readonly int _failureThreshold;
        private readonly int _recoveryTimeoutSeconds;
        
        public CircuitState State { get; private set; } = CircuitState.Closed;
        public int FailureCount { get; private set; }
        public DateTime? LastFailureTime { get; private set; }
        public int SuccessCount { get; private set; }
        
        public CircuitBreaker(
            string name, 
            int failureThreshold = 3, 
            int recoveryTimeoutSeconds = 60)
        {
            _name = name;
            _failureThreshold = failureThreshold;
            _recoveryTimeoutSeconds = recoveryTimeoutSeconds;
        }
        
        /// <summary>
        /// Check if operation should be allowed
        /// </summary>
        public bool CanExecute()
        {
            lock (this)
            {
                switch (State)
                {
                    case CircuitState.Closed:
                        return true;
                        
                    case CircuitState.Open:
                        if (DateTime.UtcNow - LastFailureTime >= TimeSpan.FromSeconds(_recoveryTimeoutSeconds))
                        {
                            Console.WriteLine($"[CircuitBreaker] '{_name}' entering HALF_OPEN state");
                            State = CircuitState.HalfOpen;
                            return true;
                        }
                        return false;
                        
                    case CircuitState.HalfOpen:
                        return true;
                        
                    default:
                        return false;
                }
            }
        }
        
        /// <summary>
        /// Record successful operation
        /// </summary>
        public void RecordSuccess()
        {
            lock (this)
            {
                SuccessCount++;
                
                if (State == CircuitState.HalfOpen)
                {
                    Console.WriteLine($"[CircuitBreaker] '{_name}' recovered - CLOSED");
                    State = CircuitState.Closed;
                    FailureCount = 0;
                }
                else
                {
                    FailureCount = 0;
                }
            }
        }
        
        /// <summary>
        /// Record failed operation
        /// </summary>
        public void RecordFailure()
        {
            lock (this)
            {
                FailureCount++;
                LastFailureTime = DateTime.UtcNow;
                
                if (State == CircuitState.HalfOpen)
                {
                    Console.WriteLine($"[CircuitBreaker] '{_name}' failed in HALF_OPEN - OPEN");
                    State = CircuitState.Open;
                }
                else if (FailureCount >= _failureThreshold)
                {
                    Console.WriteLine($"[CircuitBreaker] '{_name}' OPEN after {FailureCount} failures");
                    State = CircuitState.Open;
                }
            }
        }
        
        /// <summary>
        /// Get current status for monitoring
        /// </summary>
        public object GetStatus()
        {
            return new
            {
                Name = _name,
                State = State.ToString(),
                FailureCount,
                SuccessCount,
                LastFailureTime
            };
        }
    }
}