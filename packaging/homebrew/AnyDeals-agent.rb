class AnyDealsAgent < Formula
  include Language::Python::Virtualenv

  desc "Self-improving AI agent that creates skills from experience"
  homepage "https://github.com/JINKUI/AnyDeals-Hermes"
  url "https://github.com/NousResearch/hermes-agent/releases/download/v2026.3.30/hermes_agent-0.6.0.tar.gz"
  sha256 "<replace-with-release-asset-sha256>"
  license "MIT"

  depends_on "certifi" => :no_linkage
  depends_on "cryptography" => :no_linkage
  depends_on "libyaml"
  depends_on "python@3.14"

  pypi_packages ignore_packages: %w[certifi cryptography pydantic]

  # Refresh resource stanzas after bumping the source url/version:
  #   brew update-python-resources --print-only anydeals-agent

  def install
    venv = virtualenv_create(libexec, "python3.14")
    venv.pip_install resources
    venv.pip_install buildpath

    pkgshare.install "skills", "optional-skills"

    %w[anydeals anydeals-agent anydeals-acp].each do |exe|
      next unless (libexec/"bin"/exe).exist?

      (bin/exe).write_env_script(
        libexec/"bin"/exe,
        ANYDEALS_BUNDLED_SKILLS: pkgshare/"skills",
        ANYDEALS_OPTIONAL_SKILLS: pkgshare/"optional-skills",
        ANYDEALS_MANAGED: "homebrew"
      )
    end
  end

  test do
    assert_match "AnyDeals Agent v#{version}", shell_output("#{bin}/anydeals version")

    managed = shell_output("#{bin}/anydeals update 2>&1")
    assert_match "managed by Homebrew", managed
    assert_match "brew upgrade anydeals-agent", managed
  end
end
