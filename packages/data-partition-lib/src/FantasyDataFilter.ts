/**
 * FIREWALL: Blocks game-internal data from reaching the web platform.
 *
 * This is the primary enforcement class for the SATOR data partition.
 * Every data path from the game to the web MUST pass through this filter.
 *
 * See docs/FIREWALL_POLICY.md for the full policy and rationale.
 */
export class FantasyDataFilter {
  /**
   * Fields that exist exclusively inside the game simulation and must
   * never be transmitted to the web platform or stored in the public DB.
   */
  static GAME_ONLY_FIELDS = new Set([
    'internalAgentState',
    'radarData',
    'detailedReplayFrameData',
    'simulationTick',
    'seedValue',
    'visionConeData',
    'smokeTickData',
    'recoilPattern',
  ]);

  /**
   * Sanitize a game data object before sending it to the web platform.
   *
   * Performs a deep clone and removes all GAME_ONLY_FIELDS from the
   * top-level object. For nested objects use recursive sanitization
   * (TODO: Phase 3).
   *
   * @param gameData - Raw data object from the game simulation
   * @returns A sanitized copy safe for web consumption
   */
  static sanitizeForWeb(gameData: any): any {
    // TODO: Implement full recursive filtering logic (Phase 3)
    const sanitized = JSON.parse(JSON.stringify(gameData));
    for (const field of this.GAME_ONLY_FIELDS) {
      delete sanitized[field];
    }
    return sanitized;
  }

  /**
   * Validate that incoming web data does not contain game-internal fields.
   *
   * Throws an error if any GAME_ONLY_FIELD is found. Call this at the API
   * ingestion point before persisting any data.
   *
   * @param webData - Data received from or destined for the web layer
   * @returns `true` if all fields are valid
   * @throws Error if a forbidden field is detected
   */
  static validateWebInput(webData: any): boolean {
    // TODO: Implement recursive key validation (Phase 3)
    for (const key of Object.keys(webData)) {
      if (this.GAME_ONLY_FIELDS.has(key)) {
        throw new Error(`Web attempted to write game-internal field: ${key}`);
      }
    }
    return true;
  }
}
