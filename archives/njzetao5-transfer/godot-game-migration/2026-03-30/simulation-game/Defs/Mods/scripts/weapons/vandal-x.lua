-- Example Lua script for custom weapon behavior
-- SATOR Modding System v2.0

-- Weapon: Vandal X
-- Features: Burst fire mode, custom recoil pattern

local Weapon = require("sator.weapon")
local Events = require("sator.events")

-- Weapon state
local burstCount = 0
local burstMax = 3
local burstDelay = 0.1

-- Event: When weapon is fired
Events.on_fire:Connect(function(context)
    local weapon = context.weapon
    local shooter = context.shooter
    
    -- Burst fire logic
    if burstCount < burstMax then
        burstCount = burstCount + 1
        
        -- Custom recoil pattern
        local recoilX = math.sin(burstCount) * 0.1
        local recoilY = burstCount * 0.15
        
        weapon:applyRecoil(recoilX, recoilY)
        
        -- Burst sound
        if burstCount == 1 then
            weapon:playSound("burst_start")
        end
    else
        -- Burst complete, reset
        burstCount = 0
        weapon:setCooldown(burstDelay)
    end
    
    -- Log for analytics
    print(string.format("[Vandal-X] Fired by %s, burst: %d/%d", 
        shooter.name, burstCount, burstMax))
end)

-- Event: When weapon is reloaded
Events.on_reload:Connect(function(context)
    local weapon = context.weapon
    
    -- Reset burst counter
    burstCount = 0
    
    -- Custom reload animation speed
    weapon:setReloadSpeed(1.2) -- 20% faster
    
    print("[Vandal-X] Reloaded, burst counter reset")
end)

-- Event: When weapon is equipped
Events.on_equip:Connect(function(context)
    local weapon = context.weapon
    local agent = context.agent
    
    -- Reset state
    burstCount = 0
    
    -- Apply custom skin if available
    if agent:hasSkin("vandal-x-camo") then
        weapon:setSkin("vandal-x-camo")
    end
    
    print(string.format("[Vandal-X] Equipped by %s", agent.name))
end)

-- Custom function: Check if burst is active
function isBurstActive()
    return burstCount > 0 and burstCount < burstMax
end

-- Export for other scripts
return {
    isBurstActive = isBurstActive,
    getBurstCount = function() return burstCount end
}