namespace DawgsUprising.Sim
{
    /// <summary>
    /// Seeded random numbers, bit-exact with the web SIM's mulberry32(). Every random choice in the SIM
    /// comes from one of these (never System.Random or UnityEngine.Random), so the same seed gives the same
    /// battle on every machine and matches the web game. The constants are the algorithm's own.
    /// </summary>
    public sealed class Rng
    {
        uint _a;

        /// <summary>How many numbers have been drawn (tests compare this with the web game).</summary>
        public int Draws;

        /// <summary>Only the low 32 bits of the seed are used, like JS `a|=0`.</summary>
        public Rng(long seed) { _a = unchecked((uint)seed); }

        /// <summary>Next value as an unsigned 32-bit int.</summary>
        public uint NextU32()
        {
            Draws++;
            unchecked
            {
                _a += 0x6D2B79F5u;
                uint t = (_a ^ (_a >> 15)) * (1u | _a);
                t = (t + ((t ^ (t >> 7)) * (61u | t))) ^ t;
                return t ^ (t >> 14);
            }
        }

        /// <summary>Next value in [0, 1): the same double the web rnd() returns.</summary>
        public double Next() => NextU32() / 4294967296.0;
    }
}
