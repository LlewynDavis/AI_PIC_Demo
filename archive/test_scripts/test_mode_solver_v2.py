from core.mode_solver import run_mode_solver_analysis


result = run_mode_solver_analysis(
    core_index=3.48,
    cladding_index=1.44,
    waveguide_width_um=0.5,
    waveguide_height_um=0.22,
    wavelength_um=1.55,
    output_dir="outputs/test_mode_solver_v2",
)

print("V2 mode solver test finished.")
print("Estimated neff:", result["neff_used_for_mmi"])
print("mode_profile:", result["mode_profile_result"]["mode_profile_path"])
print("neff_vs_width:", result["neff_sweep_result"]["neff_vs_width_path"])
print("mode_result:", result["mode_result_path"])
