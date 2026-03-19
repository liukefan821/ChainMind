// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AgentAccountability
 * @author Kefan Liu
 * @notice On-chain accountability framework for LLM-powered DeFi agents.
 *         Records cryptographic commitments of agent decisions using Merkle trees
 *         for gas-efficient batch submission and O(log n) single-decision verification.
 *
 * @dev Part of the ChainMind project for NBC'26 submission.
 *      Deployed on Ethereum Sepolia testnet.
 */
contract AgentAccountability {

    // ======================== Data Structures ========================

    /// @notice Represents a single agent decision commitment
    struct DecisionCommitment {
        bytes32 inputHash;      // SHA-256 hash of the LLM input prompt
        bytes32 outputHash;     // SHA-256 hash of the LLM response
        bytes32 modelHash;      // SHA-256 hash of model metadata (name, version, params)
        uint256 timestamp;      // Block timestamp when committed
        address agent;          // Address of the agent that submitted
    }

    /// @notice Represents a batch of decisions submitted as a Merkle root
    struct MerkleBatch {
        bytes32 merkleRoot;     // Root hash of the decision Merkle tree
        uint256 batchSize;      // Number of decisions in this batch
        uint256 timestamp;      // Block timestamp of batch submission
        address agent;          // Agent address that submitted the batch
        string  modelId;        // Human-readable model identifier (e.g., "qwen2.5:7b")
    }

    // ======================== State Variables ========================

    /// @notice Owner of the contract (deployer)
    address public owner;

    /// @notice Counter for individual decision commitments
    uint256 public decisionCount;

    /// @notice Counter for Merkle batch submissions
    uint256 public batchCount;

    /// @notice Mapping from decision ID to its commitment
    mapping(uint256 => DecisionCommitment) public decisions;

    /// @notice Mapping from batch ID to its Merkle batch
    mapping(uint256 => MerkleBatch) public batches;

    /// @notice Mapping to track registered agents
    mapping(address => bool) public registeredAgents;

    /// @notice Number of registered agents
    uint256 public agentCount;

    // ======================== Events ========================

    /// @notice Emitted when a single decision is committed
    event DecisionCommitted(
        uint256 indexed decisionId,
        bytes32 inputHash,
        bytes32 outputHash,
        bytes32 modelHash,
        address indexed agent,
        uint256 timestamp
    );

    /// @notice Emitted when a Merkle batch is submitted
    event BatchSubmitted(
        uint256 indexed batchId,
        bytes32 merkleRoot,
        uint256 batchSize,
        address indexed agent,
        string modelId,
        uint256 timestamp
    );

    /// @notice Emitted when a new agent is registered
    event AgentRegistered(address indexed agent, uint256 timestamp);

    // ======================== Modifiers ========================

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    modifier onlyRegisteredAgent() {
        require(registeredAgents[msg.sender], "Agent not registered");
        _;
    }

    // ======================== Constructor ========================

    constructor() {
        owner = msg.sender;
        // Auto-register the deployer as the first agent
        registeredAgents[msg.sender] = true;
        agentCount = 1;
        emit AgentRegistered(msg.sender, block.timestamp);
    }

    // ======================== Agent Management ========================

    /// @notice Register a new agent address
    /// @param _agent The address to register as an agent
    function registerAgent(address _agent) external onlyOwner {
        require(!registeredAgents[_agent], "Agent already registered");
        registeredAgents[_agent] = true;
        agentCount++;
        emit AgentRegistered(_agent, block.timestamp);
    }

    // ======================== Core Functions ========================

    /// @notice Commit a single LLM decision on-chain
    /// @param _inputHash SHA-256 hash of the input prompt
    /// @param _outputHash SHA-256 hash of the LLM output
    /// @param _modelHash SHA-256 hash of the model metadata
    /// @return decisionId The ID of the committed decision
    function commitDecision(
        bytes32 _inputHash,
        bytes32 _outputHash,
        bytes32 _modelHash
    ) external onlyRegisteredAgent returns (uint256 decisionId) {
        decisionId = decisionCount;

        decisions[decisionId] = DecisionCommitment({
            inputHash: _inputHash,
            outputHash: _outputHash,
            modelHash: _modelHash,
            timestamp: block.timestamp,
            agent: msg.sender
        });

        emit DecisionCommitted(
            decisionId,
            _inputHash,
            _outputHash,
            _modelHash,
            msg.sender,
            block.timestamp
        );

        decisionCount++;
    }

    /// @notice Submit a batch of decisions as a Merkle root (gas-efficient)
    /// @param _merkleRoot The Merkle root of the decision batch
    /// @param _batchSize Number of decisions in the batch
    /// @param _modelId Human-readable model identifier
    /// @return batchId The ID of the submitted batch
    function submitBatch(
        bytes32 _merkleRoot,
        uint256 _batchSize,
        string calldata _modelId
    ) external onlyRegisteredAgent returns (uint256 batchId) {
        require(_batchSize > 0, "Batch size must be positive");

        batchId = batchCount;

        batches[batchId] = MerkleBatch({
            merkleRoot: _merkleRoot,
            batchSize: _batchSize,
            timestamp: block.timestamp,
            agent: msg.sender,
            modelId: _modelId
        });

        emit BatchSubmitted(
            batchId,
            _merkleRoot,
            _batchSize,
            msg.sender,
            _modelId,
            block.timestamp
        );

        batchCount++;
    }

    // ======================== Verification Functions ========================

    /// @notice Verify a single decision against a submitted Merkle batch
    /// @param _batchId The batch ID to verify against
    /// @param _leafHash The hash of the decision leaf to verify
    /// @param _proof The Merkle proof (array of sibling hashes)
    /// @param _index The index of the leaf in the tree
    /// @return isValid Whether the proof is valid
    function verifyDecision(
        uint256 _batchId,
        bytes32 _leafHash,
        bytes32[] calldata _proof,
        uint256 _index
    ) external view returns (bool isValid) {
        require(_batchId < batchCount, "Invalid batch ID");

        bytes32 computedHash = _leafHash;

        for (uint256 i = 0; i < _proof.length; i++) {
            if (_index % 2 == 0) {
                computedHash = keccak256(abi.encodePacked(computedHash, _proof[i]));
            } else {
                computedHash = keccak256(abi.encodePacked(_proof[i], computedHash));
            }
            _index = _index / 2;
        }

        isValid = (computedHash == batches[_batchId].merkleRoot);
    }

    /// @notice Verify that a decision hash matches a stored individual commitment
    /// @param _decisionId The decision ID to check
    /// @param _inputHash Expected input hash
    /// @param _outputHash Expected output hash
    /// @param _modelHash Expected model hash
    /// @return isValid Whether all three hashes match
    function verifyIndividualDecision(
        uint256 _decisionId,
        bytes32 _inputHash,
        bytes32 _outputHash,
        bytes32 _modelHash
    ) external view returns (bool isValid) {
        require(_decisionId < decisionCount, "Invalid decision ID");

        DecisionCommitment memory d = decisions[_decisionId];
        isValid = (d.inputHash == _inputHash &&
                   d.outputHash == _outputHash &&
                   d.modelHash == _modelHash);
    }

    // ======================== Query Functions ========================

    /// @notice Get the details of a specific decision
    /// @param _decisionId The decision ID to query
    function getDecision(uint256 _decisionId) external view returns (
        bytes32 inputHash,
        bytes32 outputHash,
        bytes32 modelHash,
        uint256 timestamp,
        address agent
    ) {
        require(_decisionId < decisionCount, "Invalid decision ID");
        DecisionCommitment memory d = decisions[_decisionId];
        return (d.inputHash, d.outputHash, d.modelHash, d.timestamp, d.agent);
    }

    /// @notice Get the details of a specific batch
    /// @param _batchId The batch ID to query
    function getBatch(uint256 _batchId) external view returns (
        bytes32 merkleRoot,
        uint256 batchSize,
        uint256 timestamp,
        address agent,
        string memory modelId
    ) {
        require(_batchId < batchCount, "Invalid batch ID");
        MerkleBatch memory b = batches[_batchId];
        return (b.merkleRoot, b.batchSize, b.timestamp, b.agent, b.modelId);
    }
}
