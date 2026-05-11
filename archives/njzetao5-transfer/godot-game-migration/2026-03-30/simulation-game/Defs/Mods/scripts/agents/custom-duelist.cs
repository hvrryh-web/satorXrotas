// Example C# script for custom agent AI
// SATOR Modding System v2.0

using SimCore.AI;
using SimCore.Combat;
using System.Collections.Generic;

namespace Mods.Agents
{
    /// <summary>
    /// Custom duelist agent with stealth abilities
    /// </summary>    public class CustomDuelistAgent : BaseAgent
    {
        // Stealth state
        private bool isStealthed = false;
        private float stealthDuration = 3.0f;
        private float stealthCooldown = 15.0f;
        private float lastStealthTime = -999f;
        
        // Ability: Smoke Dash
        public override void OnAbility1(AbilityContext context)
        {
            if (!CanUseAbility(1)) return;
            
            // Deploy smoke
            var smoke = DeploySmoke(context.TargetPosition);
            
            // Dash through smoke
            DashTo(context.TargetPosition, speed: 1.5f);
            
            // Brief stealth
            EnterStealth(duration: 1.0f);
            
            LogAction("Used Smoke Dash");
        }
        
        // Ability: Silent Step
        public override void OnAbility2(AbilityContext context)
        {
            if (!CanUseAbility(2)) return;
            
            // Full stealth
            EnterStealth(stealthDuration);
            
            // Silent footsteps
            SetFootstepVolume(0.1f);
            
            // Speed boost
            ApplySpeedBoost(1.3f, stealthDuration);
            
            LogAction("Used Silent Step");
        }
        
        private void EnterStealth(float duration)
        {
            if (Time.time - lastStealthTime < stealthCooldown)
            {
                Log("Stealth on cooldown");
                return;
            }
            
            isStealthed = true;
            lastStealthTime = Time.time;
            
            // Visual effect
            SetOpacity(0.3f);
            
            // Remove from enemy radar
            SetRadarVisible(false);
            
            // Schedule exit
            ScheduleAction(duration, ExitStealth);
            
            Log("Entered stealth");
        }
        
        private void ExitStealth()
        {
            isStealthed = false;
            
            // Restore visibility
            SetOpacity(1.0f);
            SetRadarVisible(true);
            SetFootstepVolume(1.0f);
            
            Log("Exited stealth");
        }
        
        // Custom decision making
        public override CombatDecision MakeCombatDecision(CombatContext context)
        {
            // Prefer flanking when stealthed
            if (isStealthed && context.CanFlank)
            {
                return new CombatDecision
                {
                    Action = CombatAction.Flank,
                    Priority = 0.9f,
                    Reason = "Stealthed - optimal flanking opportunity"
                };
            }
            
            // Default to base behavior
            return base.MakeCombatDecision(context);
        }
        
        // Override damage received
        public override void OnDamageReceived(DamageInfo damage)
        {
            // Break stealth on damage
            if (isStealthed)
            {
                ExitStealth();
                Log("Stealth broken by damage");
            }
            
            base.OnDamageReceived(damage);
        }
        
        // Mod metadata for UI
        public override AgentStats GetStats()
        {
            return new AgentStats
            {
                Role = AgentRole.Duelist,
                Difficulty = 3, // Hard
                Strengths = new[] { "Flanking", "Stealth", "Mobility" },
                Weaknesses = new[] { "Revealed on damage", "Cooldown dependent" }
            };
        }
    }
}