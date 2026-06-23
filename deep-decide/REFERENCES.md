# Research basis

deep-decide is built on a simple, well-studied idea: a panel of independent
reasoners that argue, disagree, and are then judged beats a single model talking
to itself. The papers below ground each design choice. Every citation was
verified against the arXiv API; none are invented.

## Multi-agent debate and diversity of intelligence

These are the direct basis for deep-decide's independent perspectives and forced
dissent: multiple reasoners, made to disagree, produce more truthful and more
robust answers than one.

1. Du, Y., et al. (2023). *Improving Factuality and Reasoning in Language Models through Multiagent Debate.* arXiv:2305.14325. <https://arxiv.org/abs/2305.14325>
2. Liang, T., et al. (2023). *Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate.* arXiv:2305.19118. <https://arxiv.org/abs/2305.19118>
3. Khan, A., et al. (2024). *Debating with More Persuasive LLMs Leads to More Truthful Answers.* arXiv:2402.06782. <https://arxiv.org/abs/2402.06782>
4. Chan, C.-M., et al. (2023). *ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate.* arXiv:2308.07201. <https://arxiv.org/abs/2308.07201>

## Ensembling, self-consistency, and self-critique

The case that aggregating diverse reasoning, ideally across different models,
and forcing a critique pass beats a single forward pass.

5. Wang, J., et al. (2024). *Mixture-of-Agents Enhances Large Language Model Capabilities.* arXiv:2406.04692. <https://arxiv.org/abs/2406.04692>
6. Wang, X., et al. (2022). *Self-Consistency Improves Chain of Thought Reasoning in Language Models.* arXiv:2203.11171. <https://arxiv.org/abs/2203.11171>
7. Madaan, A., et al. (2023). *Self-Refine: Iterative Refinement with Self-Feedback.* arXiv:2303.17651. <https://arxiv.org/abs/2303.17651>

## LLM-as-judge: the synthesis pass, and its limits

The basis for deep-decide's final chair pass, and the reason it preserves
dissent rather than laundering it into false agreement.

8. Zheng, L., et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.* arXiv:2306.05685. <https://arxiv.org/abs/2306.05685>
9. Gu, J., et al. (2024). *A Survey on LLM-as-a-Judge.* arXiv:2411.15594. <https://arxiv.org/abs/2411.15594>
10. Guerdan, L., et al. (2025). *Validating LLM-as-a-Judge Systems under Rating Indeterminacy.* arXiv:2503.05965. <https://arxiv.org/abs/2503.05965>

## Agent frameworks and evaluation

Context for how multi-agent systems are built and benchmarked.

11. Wu, Q., et al. (2023). *AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation.* arXiv:2308.08155. <https://arxiv.org/abs/2308.08155>
12. Liu, X., et al. (2023). *AgentBench: Evaluating LLMs as Agents.* arXiv:2308.03688. <https://arxiv.org/abs/2308.03688>
